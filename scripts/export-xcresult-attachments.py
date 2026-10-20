#!/usr/bin/env python3
"""Export selected XCTAttachment files from an Xcode result bundle.

This uses the Xcode 15 compatible xcresulttool get/export interface. Newer
xcresulttool versions may use a different `export attachments` interface, so
the script walks the result tree and exports only attachments with requested
names.
"""
import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional


def xcresult_json(bundle: Path, reference: Optional[str] = None) -> dict:
    command = ["xcrun", "xcresulttool", "get", "--path", str(bundle), "--format", "json"]
    if reference:
        command += ["--id", reference]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        legacy = command + ["--legacy"]
        result = subprocess.run(legacy, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "xcresulttool get failed")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Path to the .xcresult bundle")
    parser.add_argument("output", type=Path, help="Directory for exported files")
    parser.add_argument("--name", action="append", required=True,
                        help="Exact XCTAttachment name to export; may be repeated")
    args = parser.parse_args()
    if not args.bundle.is_dir():
        parser.error(f"result bundle does not exist: {args.bundle}")

    requested = set(args.name)
    found: dict[str, str] = {}
    visited_refs: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict):
            name = node.get("name", {}).get("_value", "")
            payload = node.get("payloadRef", {}).get("id", {}).get("_value")
            if name in requested and payload:
                found[name] = payload
            for key, child in node.items():
                if key in ("testsRef", "summaryRef") and isinstance(child, dict):
                    reference = child.get("id", {}).get("_value")
                    if reference and reference not in visited_refs:
                        visited_refs.add(reference)
                        walk(xcresult_json(args.bundle, reference))
                else:
                    walk(child)

    walk(xcresult_json(args.bundle))
    args.output.mkdir(parents=True, exist_ok=True)
    exported: set[str] = set()
    for name in args.name:
        payload = found.get(name)
        if not payload:
            continue
        destination = args.output / f"{name}.png"
        subprocess.run([
            "xcrun", "xcresulttool", "export", "--type", "file",
            "--path", str(args.bundle), "--id", payload,
            "--output-path", str(destination),
        ], check=True)
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError(f"xcresulttool produced no file for attachment {name}")
        exported.add(name)
        print(f"Exported {name}: {destination} ({destination.stat().st_size} bytes)")

    missing = [name for name in args.name if name not in exported]
    if missing:
        raise SystemExit("Missing requested XCTAttachment(s): " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
