#!/usr/bin/env bash
# Runs one stage of fixed-source-v3 as frozen in FREEZE.md. All output is private.
#   run.sh chains|lp <v3 home> <v1 home> <run id>
set -euo pipefail
stage="$1"; home="$2"; v1="$3"; run_id="$4"
cd "$home"
out="$home/$run_id"; side="$home/side"
mkdir -p -m 700 "$out"/{chains/s1-whole,chains/s2-nowhole,chains/p2-nowhole,chains/s1-whole-cuts,v0,lp,out}
manifest=$(sha256sum "$v1/manifest.json" | cut -d' ' -f1)
impl=$(sha256sum "$home/engine.c" | cut -d' ' -f1)
export home v1 out side manifest impl run_id

engine_job() {
  local scenario="$1" arm="$2" L="$3" corpus="$4" policy="$1" cut_tag=none
  local -a extra=()
  if [ "$scenario" = s1-whole-cuts ]; then
    policy=s1-whole
    cut_tag=$(sha256sum "$side/$corpus.cuts" | cut -d' ' -f1)
    export FSV3_CUTS="$side/$corpus.cuts"
  else
    unset FSV3_CUTS
  fi
  export FSV3_GROUPS="$side/$corpus.groups"
  export FSV3_RECEIPT="manifest=$manifest pool=$corpus cuts=$cut_tag impl=$impl run=$run_id"
  ulimit -v 12582912
  if [ "$arm" = pathpiece ]; then
    local v0="$out/v0/$scenario-$corpus-L$L.txt"
    nice -n 19 "$home/engine" bpe "$policy" "$L" 32768 1800 "$v1/lists/$corpus.txt" "$v0"
    awk '$1 == "E" && length($6) >= 4 {print $6}' "$v0" > "$v0.seed"
    extra=("$v0.seed")
  fi
  nice -n 19 "$home/engine" "$arm" "$policy" "$L" 4096 1800 "$v1/lists/$corpus.txt" \
    "$out/chains/$scenario/$corpus-L$L-$arm.txt" "${extra[@]}"
}
export -f engine_job

case "$stage" in
  chains)
    : > "$out/jobs.txt"
    for L in 16 8 32 64; do
      for corpus in both python javascript; do
        for scenario in s1-whole s2-nowhole p2-nowhole; do
          for arm in greedy-entry greedy-byte greedtok freq-occ freq-doc bpe pathpiece; do
            echo "$scenario $arm $L $corpus" >> "$out/jobs.txt"
          done
        done
        for arm in greedy-entry greedy-byte greedtok freq-occ freq-doc; do
          echo "s1-whole-cuts $arm $L $corpus" >> "$out/jobs.txt"
        done
      done
    done
    timeout 10800 xargs -P 8 -L 1 bash -c 'engine_job "$0" "$1" "$2" "$3"' < "$out/jobs.txt"
    ;;
  lp)
    : > "$out/lp-jobs.txt"
    for policy in s1-whole s2-nowhole; do
      for K in 256 1024 4096; do echo "$policy $K" >> "$out/lp-jobs.txt"; done
    done
    timeout 10800 xargs -P 2 -L 1 bash -c 'ulimit -v 33554432; nice -n 19 "$home/../lpenv/bin/python" solve_lp.py "$v1" "$out" "$run_id" "$impl" "$0" both 16 "$1" 3600 || echo "lp failed: $0 $1" >> "$out/lp/failures.txt"' < "$out/lp-jobs.txt"
    ;;
  *) echo "unknown stage" >&2; exit 2;;
esac
