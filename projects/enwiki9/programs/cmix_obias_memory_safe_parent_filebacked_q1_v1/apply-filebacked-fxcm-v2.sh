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
harness_source=$artifact_dir/allocator-negative-control-harness.cpp
harness_dir=$source_root/gamma
harness_target=$harness_dir/allocator-negative-control-harness.cpp
integration_patch=$artifact_dir/integration-v2.patch

if [ -e "$module_target" ] || [ -L "$module_target" ] || \
   [ -e "$harness_dir" ] || [ -L "$harness_dir" ]; then
  printf 'refusing to replace allocator module or harness target\n' >&2
  exit 65
fi

temporary=$module_target.tmp.$$
trap 'rm -f -- "$temporary" "$harness_target"; rmdir -- "$harness_dir" 2>/dev/null || true' EXIT HUP INT TERM
cp -- "$module_source" "$temporary"
chmod 0644 "$temporary"
mv -- "$temporary" "$module_target"
mkdir -- "$harness_dir"
cp -- "$harness_source" "$harness_target"
chmod 0644 "$harness_target"

if ! (cd "$source_root" && patch -p1 --forward --batch --fuzz=0 --dry-run --input "$integration_patch"); then
  rm -f -- "$module_target"
  exit 66
fi
if ! (cd "$source_root" && patch -p1 --forward --batch --fuzz=0 --input "$integration_patch"); then
  rm -f -- "$module_target"
  exit 67
fi

trap - EXIT HUP INT TERM
