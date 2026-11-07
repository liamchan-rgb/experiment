#!/usr/bin/env python3
"""Copy registered static layers into the asset catalog; never crop or fit art."""
import hashlib
import json
import shutil
import struct
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[3]
catalog = root / "Sources/Resources/Assets.xcassets"
sources = json.loads((here / "runtime-sources.json").read_text())
records = []
for entry in sources:
    name, source = entry["asset"], root / entry["source"]
    data = source.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"Not a PNG: {source}"
    size = struct.unpack(">II", data[16:24])
    expected = tuple(entry["canvasPx"])
    assert size == expected, f"Unregistered image size {size}: {source}"
    directory = catalog / (name + ".imageset")
    directory.mkdir(exist_ok=True)
    filename = entry["filename"]
    for previous in directory.glob("*.png"):
        if previous.name != filename:
            previous.unlink()
    shutil.copy2(source, directory / filename)
    (directory / "Contents.json").write_text(json.dumps({
        "images": [{"filename": filename, "idiom": "universal"}],
        "info": {"author": "xcode", "version": 1},
    }, indent=2) + "\n")
    records.append({"asset": name, "source": str(source.relative_to(root)),
                    "sha256": hashlib.sha256(data).hexdigest()})
shutil.copy2(here / "runtime-configuration.json",
             catalog / "MeadowBattleHeroConfiguration.dataset/configuration.json")
(here / "runtime-import.json").write_text(json.dumps({
    "status": "single-static-pose-candidate", "copies": records,
    "transformsAtImport": "none", "animationDelivered": False,
    "userArtApproval": None,
}, indent=2) + "\n")
print(f"Imported {len(records)} registered images without cropping or resampling.")
