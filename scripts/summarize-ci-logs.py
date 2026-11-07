#!/usr/bin/env python3
"""Put concise pure-check failures into the GitHub job summary for diagnosis."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "build/logs")
    files = sorted(root.glob("*.log"))
    pattern = re.compile(r"error:|fatal error|traceback|assertionerror|\bfailed\b|\bfail\b", re.I)
    output = ["## Pure-check diagnostic summary", ""]
    found = False
    for path in files:
        lines = path.read_text(errors="replace").splitlines()
        matches = [(index + 1, line) for index, line in enumerate(lines) if pattern.search(line)]
        if not matches:
            continue
        found = True
        output.extend([f"### `{path.name}`", "", "```text"])
        for index, line in matches[-35:]:
            output.append(f"{index}: {line[:700]}")
        output.extend(["```", ""])
    if not found:
        output.extend(["No standard error marker was found in the captured logs.", ""])
        for path in files:
            lines = path.read_text(errors="replace").splitlines()
            output.extend([f"### `{path.name}` (tail)", "", "```text"])
            output.extend(line[:700] for line in lines[-8:])
            output.extend(["```", ""])
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write("\n".join(output) + "\n")
    print("\n".join(output), flush=True)


if __name__ == "__main__":
    main()
