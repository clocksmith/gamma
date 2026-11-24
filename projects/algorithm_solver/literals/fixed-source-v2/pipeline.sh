#!/usr/bin/env bash
# Runs the full frozen matrix, its gates and its certificates. Private output.
#   pipeline.sh <v2 home> <v1 home> <run id> <bound iterations>
set -euo pipefail
home="$1"; v1="$2"; run_id="$3"; iterations="$4"
cd "$home"
out="$home/$run_id"
impl=$(sha256sum engine.c | cut -d' ' -f1)
export PYTHONDONTWRITEBYTECODE=1

./run.sh chains "$home" "$v1" "$run_id"
./run.sh polish "$home" "$v1" "$run_id"
nice -n 19 python3 verify.py "$v1" "$out" "$out/out/verification.json" "$run_id" "$impl" 12
python3 check_regression.py "$v1/run-v1/chains" "$out/chains" "$out/out/regression.json"
nice -n 19 python3 check_limits.py reach "$v1" "$out/out/reachability.json"
cp census/census.json "$out/out/census.json"

python3 - "$out/out/verification.json" > "$out/bound-jobs.txt" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))['rows']
for policy in ('s1-whole', 's2-nowhole'):
    for corpus in ('both', 'python', 'javascript'):
        for K in (256, 1024, 4096):
            best = min(r['emissions'] for r in rows if r['policy'] == policy and r['corpus'] == corpus
                       and r['L'] == 16 and r['K'] == K and r['B'] is None and r['emissions'] is not None
                       and r['arm'] in ('greedy-entry', 'greedy-byte', 'greedy-polish'))
            print(policy, corpus, K, best)
PY
export v1 out iterations
xargs -P 12 -L 1 bash -c 'ulimit -v 12582912; nice -n 19 ./bound "$0" 16 "$2" "$iterations" "$3" "$v1/lists/$1.txt" "$out/certs/$0-$1-L16-K$2.bin" >> "$out/bounds.log"' < "$out/bound-jobs.txt"

for policy in s1-whole s2-nowhole; do
  for corpus in both python javascript; do
    echo "$policy $corpus"
  done
done > "$out/check-jobs.txt"
xargs -P 6 -L 1 bash -c 'nice -n 19 python3 check_bound.py "$v1" "$1" "$0" "$out"/certs/"$0"-"$1"-L16-K*.bin > "$out/out/bound-$0-$1.jsonl"' < "$out/check-jobs.txt"
echo pipeline-done
