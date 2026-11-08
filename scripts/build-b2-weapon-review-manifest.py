#!/usr/bin/env python3
"""Describe new weapon-action studies alongside the unchanged B2 candidates."""
from pathlib import Path
import copy
import hashlib
import json

R = Path(__file__).resolve().parents[1]
OLD = R / "Art/Review/Equipment/b2-batch-v5"
OUT = R / "Art/Review/Equipment/b2-batch-v6"
ART = R / "Art/Review/Battle/b2-weapons-v1"
OUT.mkdir(parents=True, exist_ok=True)
old = json.loads((OLD / "manifest.json").read_text())
manifest = copy.deepcopy(old)
manifest.update({
    "id": "b2-batch-v6",
    "title": "B2 武器专属演出 · 批量审核",
    "date": "2026-10-27",
    "previousBatch": "b2-batch-v5",
    "previousResourceRevisionSHA256": old["resourceRevisionSHA256"],
    "scope": "原六件素材维持原样；新增两段独立武器场景演出，仅供美术审核",
})
by_id = {item["id"]: item for item in old["items"]}
scenes = (
    ("greatSwordAction", "重剑·重斩演出", "greatSword", "greatSword-1.04.png",
     "重剑贴近目标，挥击、受击亮光和落地粒子共同作用；原装备素材不变。"),
    ("legendaryStaffAction", "权杖·施法演出", "legendaryStaff", "legendaryStaff-1.48.png",
     "杖头发出蓝色光弹，在目标身体上爆发并留下少量粒子；原装备素材不变。"),
)
paths = set()
for identifier, name, original, poster, scope in scenes:
    video = original + "-scene-60fps.mp4"
    gif = original + "-scene-normal.gif"
    paths.update((poster, video, gif))
    manifest["items"].append({
        "id": identifier, "name": name, "kind": "scene",
        "icon": by_id[original]["icon"],
        "definition": copy.deepcopy(by_id[original]["definition"]),
        "scope": scope, "revision": "b2-weapon-actions-v1",
        "scene": {"video": video, "gif": gif, "poster": poster},
        "artApproval": None, "runtimeIntegrated": False,
        "sourceItemID": original,
    })
files = {path: hashlib.sha256((ART / path).read_bytes()).hexdigest() for path in sorted(paths)}
files["previousResourceRevisionSHA256"] = old["resourceRevisionSHA256"]
ledger = json.dumps(files, ensure_ascii=False, indent=2) + "\n"
(OUT / "files.json").write_text(ledger)
manifest["resourceRevisionSHA256"] = hashlib.sha256(ledger.encode()).hexdigest()
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"items": len(manifest["items"]), "newScenes": 2,
                  "revision": manifest["resourceRevisionSHA256"], "newArtApproval": None}))
