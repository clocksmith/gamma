#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  printf 'usage: %s Q0_PATCHED_SOURCE_ROOT\n' "$0" >&2
  exit 64
fi

artifact_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
source_root=$(CDPATH= cd -- "$1" && pwd -P)
module_source=$artifact_dir/gamma-filebacked-fxcm.h
module_target=$source_root/src/models/gamma-filebacked-fxcm.h
integration_patch=$artifact_dir/integration-v2.patch

if [ -e "$module_target" ] || [ -L "$module_target" ]; then
  printf 'refusing to replace allocator module target: %s\n' "$module_target" >&2
  exit 65
fi

temporary=$module_target.tmp.$$
trap 'rm -f -- "$temporary"' EXIT HUP INT TERM
cp -- "$module_source" "$temporary"
chmod 0644 "$temporary"
mv -- "$temporary" "$module_target"

if ! (cd "$source_root" && patch -p1 --forward --batch --dry-run --input "$integration_patch"); then
  rm -f -- "$module_target"
  exit 66
fi
if ! (cd "$source_root" && patch -p1 --forward --batch --input "$integration_patch"); then
  rm -f -- "$module_target"
  exit 67
fi

trap - EXIT HUP INT TERM
