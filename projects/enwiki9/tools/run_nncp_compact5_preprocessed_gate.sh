#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
    echo "usage: $0 BUILD_DIR INPUT ARCHIVE" >&2
    exit 2
fi

build_dir=$1
input=$2
archive=$3
tarball="$build_dir/nncp-2024-06-05.tar.gz"
source_dir="$build_dir/nncp-2024-06-05"
expected=7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119

mkdir -p "$build_dir"
if [ ! -f "$tarball" ]; then
    curl -L --fail --silent --show-error \
        https://www.bellard.org/nncp/nncp-2024-06-05.tar.gz \
        -o "$tarball"
fi

actual=$(sha256sum "$tarball" | cut -d' ' -f1)
if [ "$actual" != "$expected" ]; then
    echo "NNCP tarball hash mismatch: $actual" >&2
    exit 1
fi

if [ ! -d "$source_dir" ]; then
    tar -xzf "$tarball" -C "$build_dir"
fi

make -C "$source_dir"

exec env LD_LIBRARY_PATH="$source_dir" "$source_dir/nncp" \
    --profile enwik9 \
    --batch_size 1 \
    --n_layer 5 \
    --d_model 256 \
    --d_inner 768 \
    --preprocess 16384,512 \
    -T "${NNCP_THREADS:-4}" \
    c "$input" "$archive"
