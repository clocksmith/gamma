# Readable joint shared-block pilot

This checkpoint implements a matched source/dictionary experiment on the three
previously exposed readable-v1 problems #547, #841 and #1091, separately in
JavaScript and Python. It now has matched isolated pilot evidence, **not an M1 pass**.

## Historical result: qualification blocked

The fresh dot run stopped before executing any candidate because the unchanged
judge's required `/usr/bin/node` runtime is absent from its exposed filesystem.
The [retained receipt](evidence/qualification/qualification.json) records
`blocked`, `success: false`, **zero candidate executions**, and all 12 source
rows unqualified. Its 9,280 planned checks were not run. No host-execution or
weakened-isolation fallback was used.

The comparison rejects that actual receipt before creating its output directory:
**zero production fits and zero production packets**. There are no measured
selection medians, p95s, compression improvements or milestone changes to report.
See the [machine-readable status](evidence/comparison-status.json) and
[hash-bound comparison freeze](evidence/freeze/contract.json).

## Implemented and checked

- `variants.py` preserves the six original sources and constructs six complete
  shared-breadth alternatives. Every standalone successor contains its complete
  queue helper, callback, caller and official wrapper. No hidden helper channel.
- `qualify.py` freezes new synthetic/public cases and exact source/code identities,
  then requires the existing isolated judge. Independent semantic cases and the
  grid's aliased-row predecessor-compatibility control remain distinct. Details:
  [qualification contract](QUALIFICATION.md).
- `compare.py` crosses original/shared source with original-fitted/shared-refitted
  dictionaries at 128/256-entry caps. Both use the existing 96 paid printable-ASCII
  plus LF entries, complete short readable lines/blocks, bounded deterministic
  exact-marginal fitting, and fully charged LTD1/LTV1 packets. Details:
  [predeclared experiment](FREEZE.md).
- The comparison independently replays the whole qualification evidence bundle,
  rather than trusting pass flags. It requires current cases/code/sandbox hashes,
  all planned checks/executions, zero failures and all retained observations.
- Twenty focused comparison tests pass: exact minimum cost, canonical ID ties,
  round trips, malformed packets, cross-process reproducibility, budget failure,
  full byte accounting, complete evidence replay and stale/incomplete receipt
  rejection. These tests use inert synthetic text, not candidate execution.

The [development-transfer tooling](TRANSFER.md) is a separate preparation path
for the explicitly allowed data. It does not authorize protected-data access or
replace this pilot's correctness gate.

## Reproduce

Run from this directory:

```sh
python3 -B -m unittest -v test_compare test_variants
python3 -B compare.py freeze --output /tmp/readable-joint-freeze-new
python3 -B qualify.py --output /tmp/readable-joint-qualification-new
python3 -B compare.py run --freeze /tmp/readable-joint-freeze-new \
  --qualification /tmp/readable-joint-qualification-new/qualification.json \
  --output /tmp/readable-joint-comparison-new
```

Use new output directories. The last command is eligible only after genuine
isolated qualification succeeds for all frozen hashes. Until dot provides the
required runtime and isolation prerequisites, it must remain blocked. If code,
sources, cases or sandbox change, make a new freeze and qualification receipt;
do not edit old evidence or manually mark it successful. No models, training,
protected final 100/protected 66, deployment or human study are involved.

## Exact fitting optimization

Trial literals absent from a program reuse that program's exact current selection
count instead of rescoring its unchanged graph. Counts are refreshed from the
independent canonical scorer after every accepted addition. Every candidate still
receives its exact total score and consumes the same evaluation-budget unit;
pool, ordering, tie-breaks and acceptance policy are unchanged. A synthetic
full-rescore reference checks dictionaries, complete move traces and evaluation
counts for both widths, and confirms absent programs skip DP work.

This reduces redundant work; it is not a measured corpus speedup or a change to
M1 compactness. The code hash changes: historical freezes/receipts stay intact
and cannot authorize a new production fit. Create fresh artifacts only after the
unchanged isolated qualification gate can succeed.

## 2026-10-25 dot runtime continuation

The native dot desktop supports the unchanged isolation; the separate command
namespace's earlier NETLINK failure was not a desktop-wide restriction. The owner
approved a versioned, hash-pinned, read-only executable Node mount. Native controls
confirmed read-only task/runtime files, no host workspace, and loopback-only
network visibility. Historical blocked receipts above remain unchanged.

A fresh matched run passed **9,280 checks**, **76 isolated executions**, all twelve
Python/JavaScript baseline and shared-breadth rows, and no failures. Independent
oracle and aliased-grid compatibility checks remain distinct. The 128/256 comparison
completed with exact packet reconstruction and complete byte accounting. At 256,
shared-breadth JS has median 23/p95 27 and Python 19/20, both zero character bits;
this is only **three exposed problems per language**, not 400/500 qualification.
The 128 arms still have high character fractions and do not meet compactness gates.

[Compact result receipt](evidence/dot-runtime-continuation.json) binds the complete
local evidence at `/workspace/shared/gamma-dot-diagnostics/`; no private development
cases are published. New qualification accepts `--node-runtime` with the approved
executable. Runtime identity and its adapter are checked again during comparison.
