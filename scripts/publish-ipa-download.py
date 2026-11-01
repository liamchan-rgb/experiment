#!/usr/bin/env python3
"""Validate the device IPA, then publish it and its download notes to GitHub."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import plistlib
import struct
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


def publish_large_file(path: str, content: bytes, message: str) -> None:
    """Commit large files through Git; the Contents API rejects this IPA size."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    subprocess.run(["git", "add", "--sparse", "--", path], check=True)
    subprocess.run(
        ["git", "-c", "user.name=Codex", "-c", "user.email=codex@openai.com",
         "commit", "--only", "-m", message + " [skip ci]", "--", path],
        check=True,
    )
    ref = "refs/heads/" + os.environ["GITHUB_REF_NAME"]
    subprocess.run(["git", "push", "origin", "HEAD:" + ref], check=True)
    print(f"Published {path} as a Git blob ({len(content)} bytes)", flush=True)


def macho_has_arm64(path: Path) -> bool:
    """Read Mach-O CPU types directly so validation works outside macOS too."""
    data = path.read_bytes()
    magic = data[:4]
    thin_orders = {
        b"\xce\xfa\xed\xfe": "<",  # MH_MAGIC, little endian
        b"\xcf\xfa\xed\xfe": "<",  # MH_MAGIC_64, little endian
        b"\xfe\xed\xfa\xce": ">",  # MH_CIGAM, big endian
        b"\xfe\xed\xfa\xcf": ">",  # MH_CIGAM_64, big endian
    }
    if magic in thin_orders:
        return struct.unpack_from(thin_orders[magic] + "I", data, 4)[0] == 0x0100000C

    fat_orders = {
        b"\xca\xfe\xba\xbe": (">", 20),  # FAT_MAGIC
        b"\xbe\xba\xfe\xca": ("<", 20),  # FAT_CIGAM
        b"\xca\xfe\xba\xbf": (">", 32),  # FAT_MAGIC_64
        b"\xbf\xba\xfe\xca": ("<", 32),  # FAT_CIGAM_64
    }
    if magic not in fat_orders:
        raise SystemExit(f"Application executable is not a Mach-O binary: {path}")
    byte_order, stride = fat_orders[magic]
    count = struct.unpack_from(byte_order + "I", data, 4)[0]
    if count == 0 or len(data) < 8 + count * stride:
        raise SystemExit(f"Application executable has an invalid universal header: {path}")
    return any(struct.unpack_from(byte_order + "I", data, 8 + index * stride)[0] == 0x0100000C for index in range(count))


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
    if not macho_has_arm64(executable):
        raise SystemExit("IPA application executable does not contain the arm64 architecture")

    digest = hashlib.sha256()
    with ipa.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    checksum = digest.hexdigest()
    size = ipa.stat().st_size
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ["GITHUB_REF_NAME"]
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}/Downloads/MeadowJourney-build{build}.ipa"
    review = f"https://github.com/{repo}/blob/{branch}/Art/Review/Battle/spellblade-demo-v1/review.json"
    rune_slash_gif = f"https://raw.githubusercontent.com/{repo}/{branch}/Art/Review/Battle/spellblade-demo-v1/runeSlash-normal.gif"
    rune_ward_gif = f"https://raw.githubusercontent.com/{repo}/{branch}/Art/Review/Battle/spellblade-demo-v1/runeWard-normal.gif"
    flame_gif = f"https://raw.githubusercontent.com/{repo}/{branch}/Art/Review/Battle/dragon-flame-demo-v1/dragon-flame-normal.gif"
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
    ipa_bytes = ipa.read_bytes()
    old_ipa = api_request("GET", ipa_path)
    expected_blob = hashlib.sha1(b"blob " + str(size).encode() + b"\0" + ipa_bytes).hexdigest()
    if old_ipa and old_ipa.get("size") == size and old_ipa.get("sha") == expected_blob:
        print(f"Verified existing direct IPA Git blob: {old_ipa['sha']}", flush=True)
    else:
        publish_large_file(ipa_path, ipa_bytes, f"Publish Build {build} direct IPA")

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
    heading = f"## build{build} · 符文斩／庇护接入与状态时序 · {version}"
    if heading in readme:
        start = readme.index(heading)
        end = readme.find("\n---\n", start)
        readme = readme[:start] + (readme[end + 5 :] if end >= 0 else "")
    section = f"""{heading}

[直接下载 MeadowJourney-build{build}.ipa]({raw}) · [符文斩全场 GIF]({rune_slash_gif}) · [符文庇护全场 GIF]({rune_ward_gif}) · [龙焰全场 GIF]({flame_gif}) · [时序／审核记录]({review}) · [校验记录](MeadowJourney-build{build}.json)

接入符文斩V2的20帧攻击素材；符文庇护上传包与已归档源包SHA-256相同，继续沿用同一套20帧，未重复导入。上一轮的星辉脉冲、龙魂庇护、龙鳞庇护均复核并调整治疗／护盾显示时序。游戏规则与实际HP/AP/护盾仍在命中回执提交；治疗、护盾圈及数值提示延至相应特效进入后半段（58%）再出现，星辉脉冲在命中时已进入60%。

符文斩、符文庇护和龙焰全场动图均按正常速度离线合成；上一轮五段技能GIF保持 720×432、2.8 秒、按素材原始12–20 FPS。它们都不是 UIKit、模拟器或实机录屏。Swift规则测试、资源／时序审计和设备Release归档均通过。IPA为SideStore重签用的unsigned arm64设备包，{size:,}字节，SHA-256 `{checksum}`；ZIP CRC和版本号均通过。GitHub Actions [运行 #{os.environ['GITHUB_RUN_ID']}]({run_url})。未运行模拟器或实机；安装和实机效果由用户验收。

[八段技能全场GIF和审核数据]({review}) · [符文斩V2源素材与拆帧](../Art/Parts/BattleVFX/rune-slash-v2/README.md) · [符文庇护归档与重复包核验](../Art/Parts/BattleVFX/rune-ward-v1/README.md)

下一步两项：龙鳞庇护护盾接触／破碎反馈的场景审核；龙之号令增益特效设计。

---

"""
    put(readme_path, (section + readme.lstrip()).encode(), f"Publish Build {build} IPA notes", readme_sha)
    print(f"Verified and published direct IPA: {raw}", flush=True)


if __name__ == "__main__":
    main()
