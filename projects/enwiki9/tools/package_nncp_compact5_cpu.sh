#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
    echo "usage: $0 NNCP_SOURCE_DIR OUTPUT_TAR_GZ" >&2
    exit 2
fi

source_dir=$1
output=$2

files='Makefile VERSION arith.c arith.h cmdopt.c cmdopt.h cp_utils.c cp_utils.h cutils.c cutils.h libnc.h libnc.so list.h nncp.c preprocess.c preprocess.h'

for file in $files; do
    if [ ! -f "$source_dir/$file" ]; then
        echo "missing required NNCP artifact: $file" >&2
        exit 1
    fi
done

tar \
    --sort=name \
    --mtime=@0 \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    -C "$source_dir" \
    -czf "$output" \
    $files

bytes=$(stat -c %s "$output")
hash=$(sha256sum "$output" | cut -d' ' -f1)
printf 'package_bytes=%s\npackage_sha256=%s\n' "$bytes" "$hash"
