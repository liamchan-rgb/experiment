#!/usr/bin/env python3
"""Rewrap an existing device IPA as classic, stored ZIP without changing app bytes."""
import hashlib
import json
import plistlib
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

source, target = map(Path, sys.argv[1:3])
assert source.resolve() != target.resolve()
with ZipFile(source) as original:
    assert original.testzip() is None, 'Source IPA failed CRC validation'
    entries = original.infolist()
    with ZipFile(target, 'w', compression=ZIP_STORED, allowZip64=False) as output:
        for entry in entries:
            clean = ZipInfo(entry.filename, entry.date_time)
            clean.create_system = 3
            clean.compress_type = ZIP_STORED
            clean.external_attr = entry.external_attr
            clean.extra = b''
            clean.comment = b''
            output.writestr(clean, original.read(entry))
    with ZipFile(target) as rewritten:
        assert rewritten.testzip() is None
        assert rewritten.namelist() == original.namelist()
        for entry in entries:
            assert rewritten.read(entry.filename) == original.read(entry), entry.filename
            assert rewritten.getinfo(entry.filename).compress_type == ZIP_STORED
            assert not rewritten.getinfo(entry.filename).extra
        info = plistlib.loads(rewritten.read('Payload/MeadowJourney.app/Info.plist'))
print(json.dumps({'file': str(target), 'version': info['CFBundleShortVersionString'],
                  'build': info['CFBundleVersion'], 'bytes': target.stat().st_size,
                  'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'compression': 'stored', 'payloadBytesIdentical': True}, indent=2))
