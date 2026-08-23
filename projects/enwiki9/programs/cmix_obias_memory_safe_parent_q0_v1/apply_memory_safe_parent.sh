#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  printf 'usage: %s BOUND_SOURCE_ROOT\n' "$0" >&2
  exit 64
fi

artifact_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
source_root=$(CDPATH= cd -- "$1" && pwd -P)
patch_file=$artifact_dir/memory-safe-parent.patch

check_source() {
  relative_path=$1
  expected_sha256=$2
  actual_sha256=$(sha256sum "$source_root/$relative_path" | awk '{print $1}')
  if [ "$actual_sha256" != "$expected_sha256" ]; then
    printf 'source hash mismatch: %s expected=%s actual=%s\n' \
      "$relative_path" "$expected_sha256" "$actual_sha256" >&2
    exit 65
  fi
}

check_source \
  src/models/ppmd.cpp \
  d54d27616f756efa1fd5d08aaec85fe4688004b5dcd49f411caba92812cbb7e1
check_source \
  src/runner.cpp \
  3344fabe7a9474eac370269afeee2fa9fe0597e50fbc370888b2a537c04e652c

(
  cd "$source_root"
  patch -p1 --forward --batch --dry-run --input "$patch_file"
  patch -p1 --forward --batch --input "$patch_file"
)
