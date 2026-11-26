# Status: paused by the owner on 2026-11-25, about 15:29 UTC

The fresh-data test has not been run. Nothing is running.

| Step in `PREREGISTRATION.md` | State |
| --- | --- |
| 1. Corpus manifest and baseline harness committed | Done (`../fresh-short-records-v1/`, `../fair-baselines-v1/`) |
| 2. Test sets encrypted, plain copies deleted | Done, 2026-11-25 13:15:14 UTC |
| 3. Freeze owner pins the six items in `FREEZE.json` | **Not done.** Started 13:38 UTC, stopped 15:30 UTC with nothing pinned. See `FREEZE-PROGRESS.md`. |
| 4. Opening record | Not done |
| 5. Scoring on the test sets | Not done |

**The test sets are sealed and unopened. There is no `FREEZE.json`. No result on fresh test data exists.**

## What exists so far

- An adapter for the lane's codec that reproduces the lane's own scripts byte for byte on the exported records of
  the old suites (35 of 35 rows identical).
- Provisional measurements on training and validation records only, in `FREEZE-PROGRESS.md`. They decide nothing:
  the candidate search was cut short (35 configurations measured, 15 queued and not run), baseline tuning had one
  pass, and no lookup time was measured.
- The diagnostic rerun on the lane's old suites, in `../fair-baselines-v1/results/`. It concerns only whether
  per-record framing explained the old result.

`unfinished-freeze-tools/` holds the freeze owner's working code. `score.py` and `assemble_freeze.py` in it have
never been executed.

## To resume

1. A freeze owner who has not seen the test sets continues from "Next steps" in `FREEZE-PROGRESS.md`, under the
   same limits: training and validation records only, no network.
2. The lookup-time measurement and the scoring run need a quiet machine.
3. The codec's author was asked which configuration they stand behind and had not answered when the work paused.
4. Only after `FREEZE.json` is committed does the custodian commit the opening record and decrypt the test sets.

## Owner decision, 2026-11-26

From an external review the owner accepted. The test stays paused. This note restarts nothing, and the
pre-registration is unchanged.

- **The freeze stopped before fresh data.** No codec result exists from this test. The provisional
  validation-record ratios in `FREEZE-PROGRESS.md` decide nothing.
- **Codec-claim bar.** A BITS codec claim needs all four: fresh data; lean-framed zstd and FSST baselines;
  complete accounting of every byte the decoder sees; and a measured p95 lookup latency. The required check for the
  byte accounting is the golden-byte accounting fixture being added to the short-record harness. A claim without a
  pass on that fixture does not meet the bar.
- **Stop.** No tuning on held-out records. A smaller dictionary is not presented as better compression.
