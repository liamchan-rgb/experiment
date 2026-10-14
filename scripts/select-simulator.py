#!/usr/bin/env python3
"""Select or create an iPhone using a runtime compatible with the selected Xcode."""
import json
import subprocess
import sys


def version(value):
    return tuple(int(part) for part in value.split('.')[:2])


def simctl(*args):
    return subprocess.check_output(['xcrun', 'simctl', *args], text=True)


sdk = version(subprocess.check_output(
    ['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], text=True).strip())
inventory = json.loads(simctl('list', '--json'))
runtimes = [runtime for runtime in inventory['runtimes']
            if runtime.get('isAvailable') and '.iOS-' in runtime['identifier']
            and (15, 0) <= version(runtime['version']) <= sdk]
if not runtimes:
    print('No installed compatible iOS runtime; download the selected Xcode platform.', file=sys.stderr)
    sys.exit(2)
runtime = max(runtimes, key=lambda item: version(item['version']))
devices = [device for device in inventory['devices'].get(runtime['identifier'], [])
           if device.get('isAvailable') and device['name'].startswith('iPhone')]
if devices:
    device = next((device for device in devices if device['name'] == 'iPhone 16'), devices[0])
    udid = device['udid']
    name = device['name']
else:
    types = inventory['devicetypes']
    eligible = [kind for kind in types if kind.get('productFamily') == 'iPhone'
                and version(kind.get('minRuntimeVersionString', '0.0')) <= version(runtime['version'])]
    preferred = next((kind for kind in eligible if kind['name'] == 'iPhone 16'), None)
    if preferred is None:
        preferred = next((kind for kind in eligible if kind['name'] == 'iPhone 15'), None)
    if preferred is None:
        if not eligible:
            raise SystemExit('No compatible iPhone device type installed')
        preferred = eligible[-1]
    name = 'MeadowJourney CI iPhone'
    udid = simctl('create', name, preferred['identifier'], runtime['identifier']).strip()
print(f'Selected {name}, {runtime["name"]}, {udid}', file=sys.stderr)
print(udid)
