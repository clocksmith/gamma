#!/usr/bin/env bash
# The whole frozen v3 run, under its eight-hour limit. Private output.
#   pipeline.sh <v3 home> <v1 home> <v2 chains> <run id> <acorn.js>
set -euo pipefail
home="$1"; v1="$2"; v2_chains="$3"; run_id="$4"; acorn="$5"
cd "$home"
out="$home/$run_id"
impl=$(sha256sum engine.c | cut -d' ' -f1)
export PYTHONDONTWRITEBYTECODE=1
nice -n 19 "$home/../lpenv/bin/python" test_small.py ./engine --lp
python3 prepare.py "$v1" "$home/side" "$acorn"
./run.sh chains "$home" "$v1" "$run_id"
./run.sh lp "$home" "$v1" "$run_id"
nice -n 19 python3 verify.py "$v1" "$home/side" "$out" "$out/out/verification.json" "$run_id" "$impl" 8
python3 check_regression.py "$v2_chains" "$out/chains" "$out/out/regression.json"
nice -n 19 python3 encoded.py "$v1" "$home/side" "$out" 8
python3 score.py "$out"
echo pipeline-done
