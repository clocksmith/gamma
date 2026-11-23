#!/usr/bin/env bash
# Runs every chain of FREEZE.md. Private output, outside Git.
#   run.sh <private folder holding engine and lists/> <output folder>
set -euo pipefail
home="$1"; out="$2"
mkdir -p -m 700 "$out/chains"
jobs="$out/jobs.txt"; : > "$jobs"
for corpus in python javascript both; do
  for L in 2 4 8 16 32 64; do
    for mode in greedy-entry greedy-byte freq-occ freq-doc bpe bpe-free cover-mixed cover-nosingle; do
      echo "$mode $L $corpus" >> "$jobs"
    done
  done
  echo "cover-mixed 1 $corpus" >> "$jobs"
done
export home out
xargs -P 8 -L 1 bash -c 'nice -n 19 "$home/engine" "$0" "$1" 4096 2700 "$home/lists/$2.txt" "$out/chains/$2-L$1-$0.txt"' < "$jobs"
