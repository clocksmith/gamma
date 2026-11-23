#!/usr/bin/env bash
# Local search, verification and dual certificates for run-v1. Private output.
#   pipeline.sh <private folder>
set -euo pipefail
home="$1"; cd "$home"; run="$home/run-v1"
for corpus in python javascript both; do
  for L in 8 16 32 64; do
    for K in 128 192 256 384 512 768 1024 2048 4096; do echo "$corpus $L $K"; done
  done
done > "$run/polish-jobs.txt"
xargs -P 8 -L 1 bash -c 'nice -n 19 ./engine3 polish "$1" "$2" 60 "lists/$0.txt" "run-v1/chains/$0-L$1-polish-K$2.txt" "run-v1/chains/$0-L$1-greedy-entry.txt"' < "$run/polish-jobs.txt"
nice -n 19 python3 -B verify.py "$home" "$run" "$run/out/verification.json" 8
python3 - "$run/out/verification.json" > "$run/bound-jobs.txt" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))['rows']
for corpus in ('python', 'javascript', 'both'):
    for K in (128, 256, 512, 1024, 2048, 4096):
        best = min(r['emissions'] for r in rows if r['corpus'] == corpus and r['L'] == 16 and r['K'] == K
                   and r['B'] is None and r['emissions'] is not None and r['arm'] in ('greedy-entry', 'greedy-polish'))
        print(corpus, K, best)
PY
xargs -P 8 -L 1 bash -c 'nice -n 19 ./bound 16 "$1" 12000 "$2" "lists/$0.txt" "run-v1/certs/$0-L16-K$1.bin" >> run-v1/bounds.log' < "$run/bound-jobs.txt"
echo pipeline-done
