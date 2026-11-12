# Mars BITS readiness after reviewed requirements and boundary cases

This receipt re-measures Mars readiness for the target-builder revision that
qualifies targets against separately reviewed requirements and boundary cases
(`c75036381`). The previous record,
[mars-bits-readiness-20261110-alias-closure](../mars-bits-readiness-20261110-alias-closure/README.md),
remains the sealed receipt for baseline `348274c95`; its bound builder, builder
test, allowlist test and verifier hashes no longer match the current source.

- Sealed readiness receipt: [receipt.json](receipt.json)
  (`receipt_sha256`: `5fae95bee3aa3396928a39b681c3357da78d33ba1dec4929c255242793ec141a`,
  `baseline_git_head`: `c75036381`)
- Verifier: [verify_mars_readiness.py](../mars-bits-readiness-20261110/verify_mars_readiness.py),
  whose default `--check` receipt is now this file, so the frozen pilot
  proposal's `mars_verify_readiness_and_allowlist` commands run unchanged.

## What changed against the previous receipt

- Bound sources that changed: `algsolve/synth/semantic_target_pipeline.py`
  (required `reviewed_requirements` input, reviewer-blocked rows, a
  `reviewed_boundary` judge stage, reviewer and authorization records bound into
  the contract), `tests/test_semantic_target_pipeline.py`,
  `tests/test_semantic_allowlist.py`, and the verifier (default receipt path).
  The pilot proposal and `semantic_allowlist.py` are unchanged.
- Allowlist and boundary hashes are unchanged:
  `d29c4495…` and `5628ff61…`, 236 functional non-paid candidates.
- Focused suites: 253 tests passed (248 before; the 5 added reviewed-requirement
  tests), 3 skipped on macOS, 0 failures.
- Mars environment: `darwin` / `arm64`, macOS `26.6.2`; `22.99 GiB` free
  workspace disk at measurement. The Linux sandbox check fails closed as before
  (`SandboxUnavailable: required sandbox tool missing: /usr/bin/bwrap`).

## Jupiter native check (observation, not part of this receipt)

On 2026-11-12 an archive of `c75036381` was run on Jupiter (`Linux x86_64`,
`/usr/bin/bwrap` and `/usr/bin/prlimit` present) with the repository virtual
environment, outside Jupiter's checkout:

- `python -m unittest tests.test_semantic_target_pipeline`: 34 run, 0 skipped,
  OK, including both `NativeTargetBuilderTests` controls; the qualifying control
  now passes public, independent, reviewed boundary and declared-probe stages in
  the real sandbox.
- `python -m unittest tests.test_semantic_allowlist`: 7 run, OK.

No downloads, model work, training or protected payload reads were performed.
No reviewed requirements file exists yet for the real 236-candidate population;
these tests use synthetic reviewed rows.

## Reproduce

```bash
PYTHONPATH=projects/algorithm_solver .venv/bin/python projects/algorithm_solver/findings/mars-bits-readiness-20261110/verify_mars_readiness.py --check
```
