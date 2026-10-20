# Capture-checked rewrites and joint literal learning

On the same **80 exposed development problems**, the 256-entry candidate reduces
input from **6,413 to 5,461 selections (14.84%)**. Complete dictionary-plus-packet
storage falls from **11,781 to 11,353 bytes (3.63%)**. This is offline representation
and execution evidence, not automatic solving or protected generalization.

[Source contract](contract.json) · [Search contract](search-contract.json) ·
[Source lineage](generated/manifest.json) · [Native qualification](qualification/report.json) ·
[Search results](search-v1/summary.json) · [Independent audit](audit.json)

## What changed

The old renamer assigned globally unique local names. The new renamer reuses names
across noninterfering scopes, checks every reference's declaration identity before
and after rewriting, and optionally assigns consistent names by role. It preserves
object keys, class aliases, captures and free identifiers. Existing qualified
helper alternatives provide additional source choices. Every output byte still
comes from a stored literal. Historical XOR-to-map and allocation-heavy functional
alternatives are excluded because they increase asymptotic memory on those inputs.

Coherent source styles each learn an initial dictionary. Joint optimization then
selects both sources and literals using actual complete encodings, including
removals, swaps and paired additions. AST nodes and contiguous statement spans
propose candidates; admission requires reuse across distinct problems. Whole
entrypoints, complete entrypoint bodies and sole-return expressions are excluded.
Generic helper functions can be stored, with every byte charged.

The maximum proposal length increases from 160 to 512 bytes. One selected literal
is 163 bytes. Removing it without reoptimizing leaves 5,550 selections and an
11,275-byte package: the main improvement does not depend on that cap change,
but its extra 89-selection saving is separate from naming effects.

## Matched results

| Same 80 problems | Entries | Selections | Median / p95 | Character bits | Complete package |
|---|---:|---:|---:|---:|---:|
| Previous eight-bit control | 256 | 6,413 | 63 / 168 | 53.22% | 11,781 B |
| New eight-bit input winner | 256 | **5,461** | **57 / 148** | **51.05%** | **11,353 B** |
| Previous seven-bit control | 128 | 10,155 | 107.5 / 285 | See parent receipt | 13,002 B |
| New seven-bit input winner | 128 | 9,485 | 96.5 / 256 | 78.04% | 12,965 B |
| New seven-bit storage alternative | 128 | 9,509 | 93 / 281 | 76.10% | 12,513 B |

The eight-bit winner stores 2,612 dictionary bytes and 8,741 packet bytes,
including 3,280 framing bytes. Payload is 43,688 bits. Decoder and research-tool
storage are separate from these package figures. Offline search took 51.58 seconds
on 128; this is not description-to-program latency or an optimality certificate.

Independent source/dictionary ablation:

| Source pool | Dictionary | Selections | Complete package |
|---|---|---:|---:|
| Old | Old | 6,413 | 11,781 B |
| Expanded | Old | 6,079 | 11,447 B |
| Old | New | 7,415 | 13,307 B |
| Expanded | New | **5,461** | **11,353 B** |

New dictionary choices alone worsen the old source pool. The matched result
supports optimizing sources and dictionary together. It does not establish a
novel method or superiority over literature baselines.

## Inspect the actual pieces

[Winner strings](search-v1/joint-256-start0/dictionary.json) and
[complete sequences](search-v1/joint-256-start0/manifest.json) are directly
inspectable. Source paths in each manifest row resolve against this experiment;
new source files are in [generated/sources](generated/sources/).
Entry 253 is a 163-byte heap-sort helper body shared by problems 976 and 1051;
entry 209 is their 133-byte heap-sifting helper. Entry 208 is a 108-byte letter
frequency helper shared by 387 and 748. Entry 227 is a 93-byte binary-search loop
shared by 35 and 704. These include real algorithm structure, while the 51.05%
character fallback still prevents claiming a compact algorithm library.

## Verification and boundaries

- 380 new source versions plus 80 original controls: **460/460 passed**
  **56,623/56,623 check executions** on **8,412 distinct development cases**.
  Expected results stay outside the Linux sandbox. Outputs and input effects
  match both the development oracles and the original controls.
- Combining these with 160 previously qualified canonical/compact versions
  provides **540 source choices for 80 problems**, not 540 distinct problems.
- **26** renaming checks, **10** fragment-admission checks, and **37** existing
  judge/lane checks passed. Raw native observations and rejected/duplicate source
  proposals are retained. No full CI claim.
- An independent forward segmentation routine and packet decoder checked
  **800 packets**, source/receipt hashes, complete accounting, every selected
  multi-character literal's cross-problem reuse, and **3 accepted joint moves**
  with **12 source switches**. Packet execution reuses matching native receipts.

Milestone 1 remains open: 80 is below the frozen 500-problem denominator, median
57 exceeds 32, p95 148 exceeds 96, and fallback 51.05% exceeds 10%. Milestones 2–5
have no new autonomous result. Recognition, corpus admission, protected problems,
parameterized macro experiments and the deployed 256.one demo are unchanged.

## Reproduction

Run from the repository root on Linux with Gamma's existing judge dependencies:

~~~sh
node projects/algorithm_solver/literals/rewrite-v1/test-rewrites.cjs
node projects/algorithm_solver/literals/rewrite-v1/test-fragments.cjs
python3 projects/algorithm_solver/literals/rewrite-v1/audit.py
~~~

The audit uses only retained files. A fresh search must write a new directory:

~~~sh
python3 projects/algorithm_solver/literals/rewrite-v1/search.py --output /tmp/rewrite-search-new
~~~

For native requalification, inspect verify.py --help, use a new output path,
and keep the frozen source contract and existing Linux sandbox. Do not overwrite
this experiment's receipts. Fresh protected scoring requires its own frozen composer.
