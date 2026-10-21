#!/usr/bin/env bash
set -euo pipefail
# Debian amd64 build. SHA256 was checked against trixie Packages.xz,
# whose checksum was checked against InRelease, verified with the installed
# Debian archive keyring (Good signatures for trixie and stable release keys).
target="${1:-/workspace/tools/ngspice}"
archive="$(mktemp /tmp/ngspice-XXXXXX.deb)"
trap 'rm -f "$archive"' EXIT
curl -fLsS 'https://deb.debian.org/debian/pool/main/n/ngspice/ngspice_44.2+ds-1_amd64.deb' -o "$archive"
printf '%s  %s\n' '4d76721dd91416055b1088cfc58626d4db47b91afda7c73258c0968ba6e4d24e' "$archive" | sha256sum -c -
mkdir -p "$target"
dpkg-deb -x "$archive" "$target"
"$target/usr/bin/ngspice" --version
