# Jupiter compute supplement (declared before results)

Owner request, 2026-10-22: give the six-bit jobs more compute on Jupiter. This addendum
is committed while the frozen Mars run (`run-v1`) is still running and before the two
canonical A results or the compact C/U result have been seen. It changes nothing in
[FREEZE.md](FREEZE.md): `run-v1` on Mars stays the frozen, primary record, and this
supplement reports separately as `run-jupiter-v1`.

## What stays the same

The rules (W, U), cohorts, models, certificates, codecs, scoring and predictions of
[FREEZE.md](FREEZE.md). [run_jupiter.py](run_jupiter.py) calls the unchanged
`run.run_job()` and refuses to start if `contract.json`, `model.py`, `run.py`,
`verify.py` or this file changed, or if scipy and numpy differ from the pinned versions.
[verify.py](verify.py) checks both runs the same way.

## What changes: compute only

| | Mars run-v1 (frozen) | Jupiter run-jupiter-v1 |
| --- | --- | --- |
| Host | Mars, macOS, 8 cores, 24 GB | Jupiter, Linux, 32 cores, 122 GB |
| Python / scipy / numpy | 3.14.2 / 1.18.0 / 2.4.3 | 3.14.4 / 1.18.0 / 2.4.3 (venv) |
| LP limit | 1,800 s | 7,200 s |
| MILP limit (A, B phase 1, C) | 3,600 s | 14,400 s |
| B phase 2 limit | 1,800 s | 14,400 s |
| Jobs at a time | 4 | 4 |

HiGHS threads: scipy 1.18.0's `milp` and `linprog` expose no thread option, so each
solve runs exactly as on Mars. Extra compute comes from longer limits, not threads, and
the four jobs run side by side.

## Targets

Every job whose Mars result is unresolved, plus both canonical A jobs:

- `b-u-compact`: its Mars phase 2 hit the 1,800 s limit without a solution.
- `c-u-compact`: not yet finished on Mars; included without seeing its result.
- `a-u-canonical`, `a-w-canonical`: not yet finished on Mars; included without seeing
  their results.

`a-u-compact`, `a-w-compact`, `b-w-compact` and `c-w-compact` finished on Mars with
zero gap and are not rerun.

## Reporting

Results are reported side by side with `run-v1`, each verdict naming the run it comes
from. Where Jupiter resolves a job that Mars left open, the Mars entry is kept as the
frozen record and the Jupiter entry is marked as the compute supplement. A job that
reaches a Jupiter limit is reported with its bound and gap, as on Mars.

## Reproduce (Jupiter)

```sh
python3 -m venv ~/.venvs/sixbit && ~/.venvs/sixbit/bin/pip install scipy==1.18.0 numpy==2.4.3
~/.venvs/sixbit/bin/python -B run_jupiter.py --output run-jupiter-v1
python3 -B verify.py run-jupiter-v1
```
