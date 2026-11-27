#!/bin/sh
# Builds the frozen fixed-source-v3 engine with the 2,048-file cap raised to 65,536 and nothing else changed.
#   sh build_engine.sh OUT_DIR
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=$1
mkdir -p "$out"
sed 's/^  int cap = 2048;$/  int cap = 65536;/' "$here/../fixed-source-v3/engine.c" > "$out/engine.c"
changed=$(diff "$here/../fixed-source-v3/engine.c" "$out/engine.c" | grep -c '^[<>]' || true)
[ "$changed" = 2 ] || { echo "expected exactly one changed line, got $changed diff lines" >&2; exit 1; }
cc -O3 -Wall -Wno-unused-function -o "$out/engine" "$out/engine.c" -lm
echo "built $out/engine (file cap 65536)"
