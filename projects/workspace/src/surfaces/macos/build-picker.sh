#!/bin/sh
# Build an opt-in, locally ad-hoc signed owner picker. Never installs or launches it.
set -eu
[ "$#" -eq 1 ] || { echo "Usage: sh build-picker.sh /new/output.app" >&2; exit 2; }
[ "$(uname -s)" = Darwin ] || { echo "Requires macOS" >&2; exit 2; }
case "$1" in /*.app) app=$1;; *) echo "Absolute .app path required" >&2; exit 2;; esac
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -m 700 "$app"
mkdir -p "$app/Contents/MacOS"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>GammaPicker</string>
<key>CFBundleIdentifier</key><string>org.gamma.workspace-document-picker</string>
<key>CFBundleName</key><string>Gamma Document Picker</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
PLIST
entitlements=$(mktemp)
trap 'rm -f "$entitlements"' EXIT
cat > "$entitlements" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>com.apple.security.app-sandbox</key><true/>
<key>com.apple.security.files.user-selected.read-only</key><true/>
</dict></plist>
PLIST
binary="$app/Contents/MacOS/GammaPicker"
xcrun swiftc -warnings-as-errors "$source_dir/SelectedDocument.swift" "$source_dir/PickerMain.swift" -o "$binary"
/usr/bin/codesign --force --sign - --entitlements "$entitlements" "$app"
/usr/bin/codesign --verify --strict "$app"
/usr/bin/shasum -a 256 "$binary"
