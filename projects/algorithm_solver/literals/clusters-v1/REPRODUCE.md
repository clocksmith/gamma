# Reproduce the bounded cluster experiment

Run from Gamma's root with existing Node, Acorn, eslint-scope and escodegen, and
Python capable of running the existing Gamma Linux sandbox. No model or package
download is part of this experiment. On 128 the already installed interpreter
below avoids the system Python 3.14 / existing 3.13 venv mismatch. Use a fresh
`RUN` path; scripts intentionally refuse to overwrite results.

```bash
L="$PWD/projects/algorithm_solver/literals"
ARCHIVE="$L/clusters-v1"
RUN=/tmp/gamma-clusters-replay-v1
P=/home/x/.local/share/uv/python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13

# Required existing acceptance before native qualification.
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.venv/lib/python3.13/site-packages" taskset -c 14-17 "$P" -m pytest -q -p no:cacheprovider tests/test_algorithm_solver_judge.py tests/test_algorithm_solver_lane.py

# Only fit originals are staged or read here.
"$P" "$ARCHIVE/prepare-replay.py" --run "$RUN" --phase fit
node "$RUN/test-generate.cjs"
PYTHONDONTWRITEBYTECODE=1 "$P" "$RUN/test-search.py" "$L"
node "$RUN/generate.cjs" "$RUN" "$RUN/inputs" "$RUN/fit-generated-v1" fit
PYTHONDONTWRITEBYTECODE=1 taskset -c 14 "$P" "$RUN/verify.py" --pilot "$L" --generated "$RUN/fit-generated-v1" --output "$RUN/fit-qualification-v1"
PYTHONDONTWRITEBYTECODE=1 taskset -c 14 "$P" "$RUN/verify.py" --pilot "$L" --generated "$RUN/fit-generated-v1" --output "$RUN/fit-input-policy-recheck" --ids 832 922 976
PYTHONDONTWRITEBYTECODE=1 timeout 320s taskset -c 14 prlimit --as=8589934592 --cpu=310 "$P" "$RUN/search.py" --pilot "$L" --output "$RUN/search-v1"

# The preceding command freezes dictionaries and implementations. Only now stage
# the twelve heldback originals; preparation verifies the implementation hashes.
"$P" "$ARCHIVE/prepare-replay.py" --run "$RUN" --phase heldback
node "$RUN/generate.cjs" "$RUN" "$RUN/inputs" "$RUN/heldback-generated" heldback
PYTHONDONTWRITEBYTECODE=1 taskset -c 14 "$P" "$RUN/verify.py" --pilot "$L" --generated "$RUN/heldback-generated" --output "$RUN/heldback-qualification"
PYTHONDONTWRITEBYTECODE=1 "$P" "$RUN/evaluate-heldback.py" --pilot "$L" --output "$RUN/heldback-expression"

# Independently audit the published artifacts; output goes outside the archive.
PYTHONDONTWRITEBYTECODE=1 "$P" "$ARCHIVE/audit.py" --pilot "$L" --output "$RUN/published-artifact-audit.json"
```

The CPU IDs are host-specific; select permitted CPUs on another host while keeping
one search/qualification worker. The internal search contract stops at 160 trials
or 300 seconds. The outer 320-second timeout permits artifact finalization. Each
native call has its own 3 CPU-second / 8 wall-second / 1 GiB / 4 MiB output limits.
The observed complete run used substantially less than these limits.

The corrected reproduction does not intentionally recreate the preflight bug or
incorrect #976 nonmutation policy. Those historical artifacts remain in
`preflight-failure/`, `fit-generated/` and `fit-qualification-v1/` of the published
archive. Consequently historical failed-check counts differ on a clean replay;
qualified source bytes, dictionary IDs, sequences, costs and heldback coverage
are the deterministic targets. Elapsed times and sandbox-output receipt hashes
that depend on runtime details are not promised to match.

Do not add `@` or alter a source to make heldback #929 pass. That would be a new
fit experiment with changed exposure, not reproduction of this frozen result.
