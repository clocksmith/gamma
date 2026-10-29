# Bounded development execution for the 66-problem cohorts

This work closes the missing **candidate execution** boundary in the 35-problem
and 31-problem cohorts. It runs their actual Python and JavaScript `solve` wrappers
against their existing author references, keeping expected results in the controller
and sending only arguments to fresh candidate processes.

`runs/guarded/results.json` records **132 executed programs and 536 passing calls**:
151 cases per language for the 35-problem cohort and 117 per language for the
31-problem cohort. Input arguments were unchanged in those calls. Each executed
source is pinned and attests its SHA-256. Per-call observations and runtime/tool
identities are retained in `calls.jsonl` and `policy.json`.
The earlier successful run remains in `runs/initial/`, including its pinned tools.
Runs refuse existing output directories and reject unknown problem selections,
preventing overwritten receipts and empty selections reported as passing work.

Each measured solver call must remain below one second and one GiB observed RSS;
the containing process has a three-second timeout. Node runs jitless with a
512 MiB heap setting. These are bounded local development runs, not a security
sandbox, independent qualification, or a benchmark of the official maximum domain.
The source-defined extended cases are retained without relabeling them as proven
official-domain maxima.

The original `checks.json` files and another session's `run_candidates.py` files
are left to their owner. These separate results record the executions that occurred;
they do not retroactively turn earlier source-free tests into candidate runs.

## Study extensions

`build-study.py` and `lessons.py` author a separate study extension in each cohort:

- 396 `study.record.v1` records: 66 contracts, 66 approaches, 132 implementation
  references, 66 design-basis artifacts and 66 development-suite artifacts.
- Three stages per approach: reasoning, coding and validation, with ordered hints,
  problem framing, invariants, examples and pitfalls.
- Source-defined interfaces are preserved with unverified native-compatibility
  status. Authored paraphrases are labeled authored; original private statements
  are not copied or claimed reverified.
- `STUDY-SHA256SUMS` and `study-manifest.json` cover the extension without rewriting
  the concurrently maintained original cohort manifest and execution receipts.

The generator refuses to overwrite different existing authored extension records.
Changes require an explicit revision rather than silently rebinding published hashes.
No evidence or admission records are created; qualification stays unknown.

## Run and inspect

From Gamma:

```sh
python3 -m unittest discover -s projects/algorithm_solver/catalogue/development-66-20261029-v1 -p 'test_*.py'
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/run.py --output /PRIVATE/NEW-RUN
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/build-study.py
```

`--only ID ...` selects a focused execution subset. Use a new output directory to
retain earlier runs. The existing source-access metadata gate is checked for each
selected problem; protected source or evaluation payloads are not followed.

Harness controls exercise wrong answers, mutation, typed JSON comparison,
exceptions and stalled calls. They are checks of the development harness, not a
broken-copy qualification campaign for the solutions.

Remaining boundaries: native object/void/class interface verification, broader
independent cases and qualification, official-domain and resource confirmation,
and catalogue serving admission. A passing serialized wrapper is not proof of those.
