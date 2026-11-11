#!/usr/bin/env python3
"""Append one Swift source (path relative to Sources/) to MeadowJourney.xcodeproj by hand.

Never run scripts/generate-project.py: it drops Codex's hand-added package references and version.
Entries are inserted next to the P1AppearanceCompositor.swift entries; ids are sha1-derived and checked for uniqueness.
Usage: python3 -I scripts/add-swift-source.py Game/MeadowBattleHitFeel.swift
"""
import hashlib, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBX = ROOT / 'MeadowJourney.xcodeproj/project.pbxproj'
ANCHOR = 'Game/P1AppearanceCompositor.swift'

def ident(kind, rel):
    return hashlib.sha1(f'{kind}:Sources/{rel}'.encode()).hexdigest()[:24].upper()

def main(rel):
    text = PBX.read_text()
    if f'"path" = "{rel}";' in text:
        print('already present:', rel); return
    file_id, build_id = ident('file', rel), ident('build', rel)
    assert file_id not in text and build_id not in text, 'id collision'
    ref_match = re.search(r'\t\t(\w{24}) = \{\n\t\t\t"isa" = "PBXFileReference";\n\t\t\t"lastKnownFileType" = "sourcecode.swift";\n\t\t\t"path" = "' + re.escape(ANCHOR) + r'";\n\t\t\t"sourceTree" = "<group>";\n\t\t\};\n', text)
    anchor_file_id = ref_match.group(1)
    build_match = re.search(r'\t\t(\w{24}) = \{\n\t\t\t"isa" = "PBXBuildFile";\n\t\t\t"fileRef" = ' + anchor_file_id + r';\n\t\t\};\n', text)
    anchor_build_id = build_match.group(1)
    new_blocks = (f'\t\t{file_id} = {{\n\t\t\t"isa" = "PBXFileReference";\n\t\t\t"lastKnownFileType" = "sourcecode.swift";\n\t\t\t"path" = "{rel}";\n\t\t\t"sourceTree" = "<group>";\n\t\t}};\n'
                  f'\t\t{build_id} = {{\n\t\t\t"isa" = "PBXBuildFile";\n\t\t\t"fileRef" = {file_id};\n\t\t}};\n')
    text = text[:build_match.end()] + new_blocks + text[build_match.end():]
    for anchor, new in ((anchor_file_id, file_id), (anchor_build_id, build_id)):
        line = f'\t\t\t\t{anchor},\n'
        assert text.count(line) == 1, f'expected exactly one list entry for {anchor}'
        text = text.replace(line, line + f'\t\t\t\t{new},\n')
    PBX.write_text(text)
    print('added', rel, file_id, build_id)

if __name__ == '__main__':
    main(sys.argv[1])
