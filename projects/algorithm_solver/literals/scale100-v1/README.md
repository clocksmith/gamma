# One hundred development problems: literal scaling checkpoint

The frozen 80-problem dictionary also represents **100/100 exposed development
problems**. Relearning on the expanded set does **not** improve total selections.
This is broader tested representation, not Milestone 1 qualification or autonomous
solving.

[Audit and per-problem costs](evidence/audit.json) ·
[Frozen input identities](evidence/contract-summary.json) ·
[Qualified source inventory](evidence/source-inventory.json) ·
[Search contract](evidence/search-contract.json) ·
[Preserved preparation failures](evidence/preparation-failures.json)

## Population and correctness

The previous 80 problems retain their execution evidence. The 20 additional IDs
are **54, 56, 57, 59, 63, 66, 71, 72, 76, 77, 78, 84, 85, 90, 91, 93, 96, 97,
128 and 1512**. They add matrix traversal, intervals, dynamic programming,
sliding windows, backtracking, monotonic stacks and counting. Selection used
already-qualified development implementations and excluded protected aliases.

- **136/136** new original/rewritten source versions passed **13,495/13,495**
  check executions on **2,016** distinct assigned development cases.
- Combined with the earlier evidence: **100 problems**, **656 qualified source
  choices**, **10,428 distinct development cases**. Source choices are not problems.
- Only entrypoint normalization, printing, capture-checked naming and guarded
  arrow conversion change source. Original code, tests and rejected attempts stay
  intact. New expected values are never generated from candidate output.
- Mutation and return alias topology are checked against original execution.
  #56 retains sorting the caller array; #66 retains updating and returning the
  same array; #57 retains aliases to unchanged interval rows. The existing #78/#90
  comparator ignores outer order only, preserving inner order and multiplicity.
- Four alias checks and five host-comparator checks passed. Existing judge/lane
  acceptance checks passed before the campaign. No full CI or maximum-input
  complexity/performance qualification is claimed.

The new native run took 65.18 seconds. Every expected output remained host-side.
These are finite existing development tests; they do not prove correctness on
every input. This experiment does not modify corpus admission or its ledger.

## Matched dictionary comparison

All rows use the same 100 problems and independently qualified source pool.
Fixed-width IDs concatenate exact stored strings; names, constants, helpers,
syntax, 96 ASCII/newline entries, dictionary bytes and packet headers are counted.

| Candidate | Entries / width | Selections | Median / p95 | Character bits | Package |
|---|---:|---:|---:|---:|---:|
| Frozen 80-problem dictionary | 256 / 8 | **7,374** | **62 / 152** | 52.22% | 14,086 B |
| Joint search, best input | 256 / 8 | **7,374** | **62 / 152** | 52.22% | 14,086 B |
| Joint search, smaller package | 256 / 8 | 7,388 | 61 / 156 | 52.33% | **14,047 B** |
| Frozen / best joint seven-bit | 128 / 7 | 12,478 | 113 / 256 | 78.44% | 16,411 B |
| Seven-bit storage alternative | 128 / 7 | 12,488 | 109.5 / 274 | 76.69% | 15,946 B |

The eight-bit winner has **58,992 payload bits**, **2,612 dictionary bytes** and
**11,474 packet bytes**, including 4,100 header bytes. Decoder/tool storage is
separate. Search took 48.26 seconds on 128; it is offline encoding, not query latency.

The original 80 still cost 5,461 selections. The added 20 cost 1,913 selections,
median 87 and p95 156, with 55.57% character fallback. The alternative learned
dictionary reduces those 20 to 1,759 selections but raises the original 80 to
5,629: a real tradeoff, not an overall input win.

Independent forward segmentation and packet decoding checked **1,000 packets**,
source/receipt hashes, the complete cost calculation, all frozen problem IDs,
cross-problem literal reuse and the one accepted joint search move. All packages
exclude whole entrypoints and complete entrypoint bodies. Execution receipts are
reused by exact decoded-source identity; the audit is not another execution run.

## What this changes

The existing dictionary transfers to a broader development set with no coverage
failure. ASCII fallback contributes heavily, so this is not evidence of a compact
algorithm library. Milestone 1 still requires 400/500 frozen problems, median
32 or fewer selections, p95 96 or fewer and at most 10% character bits. Current
figures are 100/100 development problems, median 62, p95 152 and 52.22%.

Next source work should target recurring algorithm code and the expensive tail:
heap operations, dynamic-programming rows, windows and backtracking. Preserve
complexity, mutation, aliases and numerical requirements. Compare real shared
helpers against the frozen naming-only pool before another broad search sweep.
A shorter dictionary does not establish description-to-program prediction;
Milestones 2–5 and protected evaluation remain separate.

## Reproduction and retained private evidence

Raw owner-delivered sources, tests, dictionaries containing them, packets and
native observations remain under the audit's private_run_path on 128. Public
evidence contains hashes, costs and verdicts, with no solution/test disclosure.
The two historical test hash formats are explicit: sorted compact JSON for wave
receipts, sorted default JSON for #1512. Original hashes and expectations are
preserved. Three pre-execution adapter/preparation failures are retained.

From Gamma's root, with the existing Linux judge environment:

~~~sh
node projects/algorithm_solver/literals/scale100-v1/test-harness.cjs
python3 -m pytest -q projects/algorithm_solver/literals/scale100-v1/test_qualification.py
python3 projects/algorithm_solver/literals/scale100-v1/prepare.py --private-root /home/x/deco/gamma/projects/algorithm_solver --output output/literal-100-fresh
node projects/algorithm_solver/literals/scale100-v1/generate.cjs output/literal-100-fresh
python3 projects/algorithm_solver/literals/scale100-v1/qualify.py --run output/literal-100-fresh
node projects/algorithm_solver/literals/scale100-v1/pool.cjs output/literal-100-fresh
python3 projects/algorithm_solver/literals/scale100-v1/search.py --run output/literal-100-fresh
python3 projects/algorithm_solver/literals/scale100-v1/audit.py --run output/literal-100-fresh --publish output/literal-100-audit-fresh
~~~

Existing run directories are never overwritten. Do not substitute new private
inputs for historical identities and call the result a reproduction.
