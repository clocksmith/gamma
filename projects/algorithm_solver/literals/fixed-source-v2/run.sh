#!/usr/bin/env bash
# Runs fixed-source-v2 as frozen in FREEZE.md. All output is private, outside Git.
#   run.sh pilot|chains|polish <v2 home> <v1 home> <run id>
set -euo pipefail
stage="$1"; home="$2"; v1="$3"; run_id="$4"
cd "$home"
out="$home/$run_id"
mkdir -p -m 700 "$out"/{chains/s1-whole,chains/s1-nowhole,chains/s2-nowhole,certs,out}
manifest=$(sha256sum "$v1/manifest.json" | cut -d' ' -f1)
impl=$(sha256sum "$home/engine.c" | cut -d' ' -f1)
export home v1 out manifest impl run_id
ulimit -v 12582912

chain() {
  local policy="$1" arm="$2" L="$3" corpus="$4"
  FSV2_RECEIPT="manifest=$manifest pool=$corpus impl=$impl run=$run_id" \
    nice -n 19 "$home/engine" "$arm" "$policy" "$L" 4096 2700 "$v1/lists/$corpus.txt" \
    "$out/chains/$policy/$corpus-L$L-$arm.txt"
}
polish() {
  local policy="$1" corpus="$2" L="$3" K="$4"
  FSV2_RECEIPT="manifest=$manifest pool=$corpus impl=$impl run=$run_id" \
    nice -n 19 "$home/engine" polish "$policy" "$L" "$K" 60 "$v1/lists/$corpus.txt" \
    "$out/chains/$policy/$corpus-L$L-polish-K$K.txt" "$out/chains/$policy/$corpus-L$L-greedy-entry.txt"
}
export -f chain polish

# The isolation policy runs only where the census shows a whole-file string fits.
isolated() {
  case "$1:$2" in javascript:32|both:32|python:64|javascript:64|both:64) return 0;; *) return 1;; esac
}

case "$stage" in
  pilot)
    printf '%s\n' 's1-whole greedy-entry 16 both' 's2-nowhole greedy-entry 16 both' \
      's1-whole cover-nosingle 16 both' 's2-nowhole cover-nosingle 16 both' > "$out/jobs.txt"
    xargs -P 4 -L 1 bash -c 'chain "$0" "$1" "$2" "$3"' < "$out/jobs.txt"
    ;;
  chains)
    : > "$out/jobs.txt"
    for L in 16 8 32 4 64 2; do
      for corpus in both python javascript; do
        for arm in greedy-entry greedy-byte freq-occ freq-doc bpe cover-mixed cover-nosingle; do
          echo "s1-whole $arm $L $corpus" >> "$out/jobs.txt"
          echo "s2-nowhole $arm $L $corpus" >> "$out/jobs.txt"
          if isolated "$corpus" "$L"; then echo "s1-nowhole $arm $L $corpus" >> "$out/jobs.txt"; fi
        done
      done
    done
    for corpus in both python javascript; do echo "s1-whole cover-mixed 1 $corpus" >> "$out/jobs.txt"; done
    xargs -P 12 -L 1 bash -c 'chain "$0" "$1" "$2" "$3"' < "$out/jobs.txt"
    ;;
  polish)
    : > "$out/polish-jobs.txt"
    for corpus in both python javascript; do
      for L in 8 16 32 64; do
        for K in 128 192 256 384 512 768 1024 2048 4096; do
          echo "s1-whole $corpus $L $K" >> "$out/polish-jobs.txt"
          echo "s2-nowhole $corpus $L $K" >> "$out/polish-jobs.txt"
          if isolated "$corpus" "$L"; then echo "s1-nowhole $corpus $L $K" >> "$out/polish-jobs.txt"; fi
        done
      done
    done
    xargs -P 12 -L 1 bash -c 'polish "$0" "$1" "$2" "$3"' < "$out/polish-jobs.txt"
    ;;
  *) echo "unknown stage" >&2; exit 2;;
esac
