#!/usr/bin/env python3
"""Validate resource bindings and shared scheme without requiring Xcode or Pillow."""
import json
import plistlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
project = root / 'MeadowJourney.xcodeproj'
pbx = (project / 'project.pbxproj').read_text()
plist = plistlib.loads((root / 'Sources/Resources/Info.plist').read_bytes())
assert re.fullmatch(r'[A-Za-z][A-Za-z0-9 -]*', plist['CFBundleDisplayName']), \
    'SideStore App ID registration requires an ASCII-safe display name for this package'
assert plist['UISupportedInterfaceOrientations'] == [
    'UIInterfaceOrientationLandscapeLeft', 'UIInterfaceOrientationLandscapeRight']
for file in (p for p in (root / 'Sources').rglob('*') if p.suffix in ['.swift', '.metal']):
    assert str(file.relative_to(root / 'Sources')) in pbx, f'Unbound Swift file: {file}'
for catalog in (root / 'Sources/Resources/Assets.xcassets').rglob('Contents.json'):
    data = json.loads(catalog.read_text())
    for entry in data.get('images', []):
        if 'filename' in entry:
            assert (catalog.parent / entry['filename']).is_file(), f'Missing image: {entry}'
scheme = ET.parse(project / 'xcshareddata/xcschemes/MeadowJourney.xcscheme')
refs = scheme.findall('.//BuildableReference')
assert len(scheme.findall('.//TestableReference')) == 2
for ref in refs:
    assert ref.attrib['BlueprintIdentifier'] in pbx, 'Scheme target ID missing from project'
    assert ref.attrib['ReferencedContainer'] == 'container:MeadowJourney.xcodeproj'
assert 'com.apple.product-type.application' in pbx
assert '"IPHONEOS_DEPLOYMENT_TARGET" = "15.0"' in pbx
definition = json.loads((root / 'Sources/Resources/SceneMap.json').read_text())
assert 'Resources/SceneMap.json' in pbx
assert len(definition['roads']) >= 4
for prop in definition['props']:
    assert (root / 'Sources/Resources/Assets.xcassets' / (prop['asset'] + '.imageset')).is_dir()
assert not (root / 'Sources/Resources/Assets.xcassets/MapBackground.imageset').exists(), 'Flattened scene must not ship'
print('Project paths, Swift file references, asset bindings, orientations and shared test scheme valid.')
