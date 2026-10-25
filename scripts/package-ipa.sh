#!/usr/bin/env bash
# Unsigned Payload archive for SideStore; do not pass this to App Store Connect.
set -euo pipefail
archive_path="${1:?Usage: package-ipa.sh app.xcarchive output.ipa}"
output_path="${2:?Usage: package-ipa.sh app.xcarchive output.ipa}"
app_path="$archive_path/Products/Applications/MeadowJourney.app"
test -d "$app_path"
test -f "$app_path/MeadowJourney"
test -f "$app_path/Assets.car"
python3 - "$app_path/Info.plist" <<'PY'
import plistlib, re, sys
with open(sys.argv[1], 'rb') as file:
    info = plistlib.load(file)
for key in ['CFBundleName', 'CFBundleDisplayName']:
    name = info.get(key, '')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9 -]*', name):
        raise SystemExit(f'{key} is not safe for SideStore App ID registration: {name!r}')
if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
    raise SystemExit('Expected a physical-device iPhoneOS archive')
print('SideStore package metadata verified:', info['CFBundleDisplayName'],
      info['CFBundleShortVersionString'], 'build', info['CFBundleVersion'])
PY
mkdir -p "$(dirname "$output_path")"
output_dir="$(cd "$(dirname "$output_path")" && pwd)"
output_name="$(basename "$output_path")"
stage_dir="$(mktemp -d)"
trap 'rm -rf "$stage_dir"' EXIT
mkdir -p "$stage_dir/Payload"
ditto "$app_path" "$stage_dir/Payload/MeadowJourney.app"
(
  cd "$stage_dir"
  # Stored ZIP with no Unix extra fields avoids the decompression path in
  # SideStore's archive reader; Assets.car is already internally compressed.
  /usr/bin/zip -q -0 -r -X -y "$output_dir/$output_name" Payload
)
# Normalize both local and central headers to classic ZIP 2.0, as used by
# the compatibility rewrap. Keep all application bytes and Unix permissions.
python3 "$(dirname "$0")/repack-ipa.py" "$output_dir/$output_name" "$stage_dir/classic.ipa"
mv "$stage_dir/classic.ipa" "$output_dir/$output_name"
unzip -t "$output_dir/$output_name"
shasum -a 256 "$output_dir/$output_name"
echo "Unsigned IPA ready for SideStore re-signing: $output_dir/$output_name"

