# Mars BITS readiness after exact-alias holdout closure

This receipt re-measures Mars readiness for the planner revision that rejects
exact-alias leakage into combination holdouts (`348274c95`). The earlier record,
[mars-bits-readiness-20261110](../mars-bits-readiness-20261110/README.md),
remains the sealed receipt for baseline `52ab15e8`; its bound planner, planner
test and verifier hashes no longer match the current source.

- Sealed readiness receipt: [receipt.json](receipt.json)
  (`receipt_sha256`: `4a34b97e69dcecbf604200a88dd1d8674f51f6b3cbe6f3fd03cf2d197cef6605`,
  `baseline_git_head`: `348274c95`)
- Verifier: [verify_mars_readiness.py](../mars-bits-readiness-20261110/verify_mars_readiness.py),
  whose default `--check` receipt is now this file, so the frozen pilot
  proposal's `mars_verify_readiness_and_allowlist` commands run unchanged.

## What changed against the earlier receipt

- Bound sources that changed: `algsolve/synth/semantic_target_pipeline.py`,
  `tests/test_semantic_target_pipeline.py`, and the verifier (default receipt
  path; receipt arguments are resolved before use). The pilot proposal and
  `semantic_allowlist.py` are unchanged.
- Allowlist and boundary hashes are unchanged:
  `d29c4495…` and `5628ff61…`, 236 functional non-paid candidates.
- Focused suites: 248 tests passed (244 before; the 4 added alias-closure
  tests), 3 skipped on macOS, 0 failures.
- Mars environment: `darwin` / `arm64`, macOS `26.6.2`, Apple M3;
  `8.94 GiB` free workspace disk at measurement (`14.04 GiB` in the earlier
  receipt). The Linux sandbox check fails closed as before
  (`SandboxUnavailable: required sandbox tool missing: /usr/bin/bwrap`).

## Jupiter native check (observation, not part of this receipt)

On 2026-11-10 an archive of `348274c95` was run on Jupiter (`Linux x86_64`,
`/usr/bin/bwrap` and `/usr/bin/prlimit` present) with the repository virtual
environment, outside Jupiter's checkout:

- `python -m unittest tests.test_semantic_target_pipeline`: 29 run, 0 skipped,
  OK, including `NativeTargetBuilderTests` (both native target-qualification
  controls).
- `python -m unittest tests.test_semantic_allowlist`: 7 run, OK.

No downloads, model work, training or protected payload reads were performed.

## Reproduce

```bash
PYTHONPATH=projects/algorithm_solver .venv/bin/python projects/algorithm_solver/findings/mars-bits-readiness-20261110/verify_mars_readiness.py --check
```
