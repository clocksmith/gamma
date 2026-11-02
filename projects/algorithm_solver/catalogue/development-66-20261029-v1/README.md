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

Use `build-study.py --revise` for a reviewed source correction. It appends record
versions, retains previous files, and pins older source/provenance bytes through
Git or local content-addressed history. If another author owns a different teaching
file, this extension writes its own immutable teaching snapshot instead of replacing
that file. Its manifest covers only this extension's record namespace. Legacy IDs
containing `v1` remain stable identifiers; the explicit `version` field is authoritative.

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

## Native-ABI split (2026-11-02)

[NATIVE-ABI-CONTRACT-v1.md](NATIVE-ABI-CONTRACT-v1.md) records the design rules
and the applied guards. `run-case.cjs` now calls `candidate.solve` when it exists,
so object-footer modules such as the qualified `875.js` load unchanged. 156, 280 and 286
separate a pure `solve` from an in-place native entry, and 340 pins code-point
strings with non-BMP canaries. The 903 inventory/catalog hashes are reconciled with
explicit `supersedes` lineage.

`runs/native-abi-20261102/results.json` records 8 programs and 40 passing calls for
156, 280, 340 and 903 on the revised sources. `runs/native-abi-286-20261102/results.json` records 2 programs and 6 passing
calls for the revised 286 sources. `runs/native-nodes-20261102/results.json` records 22 programs
and 86 passing calls for the 11 native node problems (250, 270, 272, 298, 314, 333, 366,
369, 742, 1214, 1740), which the checker also drives on foreign node objects. `runs/string-units-20261102/results.json` records 42
programs and 210 passing calls for the 21 string-parameter problems, whose semantics pin
`string_unit` (unicode_codepoint, ascii or opaque). `runs/float-ties-20261102/results.json` records 10 programs and
40 passing calls for 270, 272, 774, 1230 and 1924 after the 1924 float-centre fix and the
tolerance/tie comparator declarations. The study extensions were revised
with `build-study.py --revise`; earlier records and receipts are retained.
`runs/guarded/` keeps its original source hashes as history.

```sh
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/check_native_abi.py
```

The checker is a regression gate over declared contracts. It is not a purity
proof or qualification.
