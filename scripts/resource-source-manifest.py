#!/usr/bin/env python3
"""Hash the exact resource inputs; compilation metadata may vary across SDKs."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "Sources/Resources"
result = {}
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != ".DS_Store":
        data = path.read_bytes()
        result[path.relative_to(root).as_posix()] = {
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
        }
print(json.dumps(result, sort_keys=True, indent=2))
