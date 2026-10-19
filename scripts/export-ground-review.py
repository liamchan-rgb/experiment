#!/usr/bin/env python3
"""Export only terrain regression attachments, keeping the review artifact small."""
import json
import subprocess
import sys
from pathlib import Path

bundle, output, family = sys.argv[1:]
destination = Path(output)
destination.mkdir(parents=True, exist_ok=True)
visited = set()
exported = set()


def read(reference=None):
    command = ['xcrun', 'xcresulttool', 'get', '--path', bundle, '--format', 'json']
    if reference:
        command += ['--id', reference]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        result = subprocess.run(command + ['--legacy'], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def walk(node):
    if isinstance(node, list):
        for child in node:
            walk(child)
    elif isinstance(node, dict):
        name = node.get('name', {}).get('_value', '')
        payload = node.get('payloadRef', {}).get('id', {}).get('_value')
        if name.startswith(('main-ground-', 'gait-hero-')) and payload and payload not in exported:
            exported.add(payload)
            path = destination / (family + '-' + name + '.png')
            subprocess.run(['xcrun', 'xcresulttool', 'export', '--type', 'file', '--path', bundle,
                            '--id', payload, '--output-path', str(path)], check=True)
            print(path)
        for key, child in node.items():
            if key in ('testsRef', 'summaryRef'):
                reference = child.get('id', {}).get('_value')
                if reference and reference not in visited:
                    visited.add(reference)
                    walk(read(reference))
            else:
                walk(child)


walk(read())
if not exported:
    raise SystemExit('No final ground regression attachments found')
