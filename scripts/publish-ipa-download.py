#!/usr/bin/env python3
"""Validate the device IPA, then publish it and its download notes to GitHub."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import plistlib
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def api_request(method: str, path: str, body: dict | None = None):
    token = os.environ["GH_TOKEN"]
    url = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + "/contents/" + urllib.parse.quote(path, safe="/")
    if method == "GET":
        url += "?ref=" + urllib.parse.quote(os.environ["GITHUB_REF_NAME"], safe="")
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "MeadowJourney-BuildPublisher",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read(4096).decode("utf-8", "replace")
        if method == "GET" and error.code == 404:
            return None
        raise RuntimeError(f"GitHub Contents API {method} {path} returned {error.code}: {detail}") from error


def existing_text(path: str) -> tuple[str, str | None]:
    item = api_request("GET", path)
    if item is None:
        return "", None
    content = base64.b64decode(item.get("content", "")).decode("utf-8")
    return content, item["sha"]


def put(path: str, content: bytes, message: str, sha: str | None = None) -> None:
    request = {
        "message": message + " [skip ci]",
        "content": base64.b64encode(content).decode("ascii"),
        "branch": os.environ["GITHUB_REF_NAME"],
    }
    if sha:
        request["sha"] = sha
    print(f"Publishing {path} ({len(content)} bytes)", flush=True)
    result = api_request("PUT", path, request)
    print(f"Published {path}: {result['commit']['sha']}", flush=True)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: publish-ipa-download.py <device.ipa> <app-executable>")
    ipa = Path(sys.argv[1])
    executable = Path(sys.argv[2])
    if os.environ.get("GITHUB_REF_TYPE") == "tag":
        raise SystemExit("Direct IPA publication requires a branch ref")

    with zipfile.ZipFile(ipa) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"IPA CRC failure: {bad}")
        info_path = next((name for name in archive.namelist() if name.endswith(".app/Info.plist") and name.startswith("Payload/")), None)
        if not info_path:
            raise SystemExit("IPA is missing its application Info.plist")
        info = plistlib.loads(archive.read(info_path))
    build = str(info.get("CFBundleVersion", ""))
    version = str(info.get("CFBundleShortVersionString", ""))
    if not build.isdigit():
        raise SystemExit(f"Unexpected bundle build number: {build!r}")
    if info.get("CFBundleSupportedPlatforms") != ["iPhoneOS"]:
        raise SystemExit("IPA is not a physical-device iPhoneOS build")
    # lipo takes input files before the operation flag; its synopsis is
    # `lipo input_file -verify_arch arch_type ...`.
    subprocess.run(["lipo", str(executable), "-verify_arch", "arm64"], check=True)

    digest = hashlib.sha256()
    with ipa.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    checksum = digest.hexdigest()
    size = ipa.stat().st_size
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ["GITHUB_REF_NAME"]
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}/Downloads/MeadowJourney-build{build}.ipa"
    review = f"https://github.com/{repo}/blob/{branch}/Art/Review/Battle/skill-vfx-v1/README.md"
    run_url = f"{os.environ['GITHUB_SERVER_URL']}/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    ipa_path = f"Downloads/MeadowJourney-build{build}.ipa"

    record = {
        "build": int(build),
        "marketingVersion": version,
        "file": ipa_path,
        "bytes": size,
        "sha256": checksum,
        "format": "unsigned iOS device IPA for SideStore re-signing",
        "architecture": "arm64",
        "zipCRC": "passed",
        "sourceCommit": os.environ["GITHUB_SHA"],
        "workflowRun": run_url,
        "skillVFXReview": "Art/Review/Battle/skill-vfx-v1/README.md",
    }
    old_ipa = api_request("GET", ipa_path)
    put(ipa_path, ipa.read_bytes(), f"Publish Build {build} direct IPA", old_ipa["sha"] if old_ipa else None)

    record_path = f"Downloads/MeadowJourney-build{build}.json"
    old_record = api_request("GET", record_path)
    put(record_path, (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode(), f"Record Build {build} IPA validation", old_record["sha"] if old_record else None)

    sums_path = "Downloads/SHA256SUMS"
    sums, sums_sha = existing_text(sums_path)
    line = f"{checksum}  MeadowJourney-build{build}.ipa"
    sums = "\n".join([line] + [row for row in sums.splitlines() if not row.endswith(f"MeadowJourney-build{build}.ipa")]) + "\n"
    put(sums_path, sums.encode(), f"Add Build {build} IPA checksum", sums_sha)

    readme_path = "Downloads/README.md"
    readme, readme_sha = existing_text(readme_path)
    heading = f"## build{build} · 五套战斗技能特效接入 · {version}"
    if heading in readme:
        start = readme.index(heading)
        end = readme.find("\n---\n", start)
        readme = readme[:start] + (readme[end + 5 :] if end >= 0 else "")
    section = f"""{heading}

[直接下载 MeadowJourney-build{build}.ipa]({raw}) · [五套正常速度全场 GIF]({review}) · [校验记录](MeadowJourney-build{build}.json)

接入星辉脉冲、振奋、横扫、龙魂庇护和龙鳞庇护五套用户素材。星辉脉冲沿用远程攻击动作，横扫沿用怪物近身攻击动作，三项辅助技能沿用防护动作；没有新增人物动作。范围特效每个目标节点只播放一次，治疗、护盾和增益仍按真实结算回执显示。原 ZIP、交付帧与运行图集均保存在 `Art/Parts/BattleVFX/`，100 张运行帧逐帧校验通过。

五段全场动图均为 720×432、2.8 秒、按素材原始 12–20 FPS 播放；它们是离线美术审核，不是 UIKit、模拟器或实机录屏。纯 Swift 规则测试、战斗／资源校验和设备 Release 归档均通过。IPA 为可由 SideStore 重签的 unsigned arm64 设备包，{size:,} 字节，SHA-256 `{checksum}`；ZIP CRC 和版本号均通过。GitHub Actions [运行 #{os.environ['GITHUB_RUN_ID']}]({run_url})。未运行模拟器或实机；安装和实机效果由用户验收。

[五套动图预览与说明](../Art/Review/Battle/skill-vfx-v1/README.md) · [原始素材和拆帧](../Art/Parts/BattleVFX/skill-effects-v1/manifest.json)

下一步两项：龙鳞庇护的护盾接触／破碎反馈；龙之号令的增益特效。

---

"""
    put(readme_path, (section + readme.lstrip()).encode(), f"Publish Build {build} IPA notes", readme_sha)
    print(f"Verified and published direct IPA: {raw}", flush=True)


if __name__ == "__main__":
    main()
