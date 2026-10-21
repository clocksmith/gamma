# Literal development expansion: 125 to 150

All 150 known development problems are represented with at most 256 concrete literal strings. This is offline source selection and encoding, not autonomous assembly or M1 qualification. The frozen original 100 and shared 125 subsets are reported separately.

## Qualification and source accounting

The next 25 ascending IDs from the previously reserved development pool were frozen before inspecting their source or cases. The mix is 6 easy, 13 medium and 6 hard; 17 of 25 are linked-list/tree problems. This is the remaining pool's skew, not a representative sample. Three catalog entries remain reserved for a later stage. Previously exposed corpus problems are not called unseen.

The first attempt accepted 22/25 additions and 141/162 source variants. Problems 105, 106 and 109 failed because their original sources relied on an external TreeNode class. These failures and their complete logs remain preserved. A separately frozen second attempt appended the exact existing constructor to each affected source, including its original control. Every constructor byte is stored and encoded; the execution harness does not inject it. This changes packaging, not the algorithms. Raw originals remain immutable.

Final qualification: **162/162 variants, 11,878/11,878 checks, 1,879 distinct cases**, in 55.06 seconds with one worker. Original result type, mutation and alias topology remain identical. Historical qualification contracts for 23 (nested list-node inputs) and 30 (unordered outer result comparison) were restored by exact receipt/case hashes before testing; neither had quarantined cases. Variant-to-original output order remains strict even for 30. The 37 existing judge/lane tests also pass.

Independent host replay verifies all 11,878 oracle/parity observations, 1,626 native log hashes, 3,002 observations containing aliases, and **1,200 packets/source choices** across eight arms. The complete pool contains 1,006 qualified source alternatives. Finite tests support tested equivalence, not a general proof or maximal-input complexity qualification. No algorithms were replaced; source normalization preserves the existing algorithms.

## Matched comparison

The original control keeps all prior 125 alternatives and adds only each new original source (including the explicitly charged constructor where required). Normalized arms add canonical/compact/scope/role/guarded-arrow alternatives. Frozen arms retain the previous stage's dictionary; relearned arms use bounded exact marginal add/remove/swap search with exact shortest-path segmentation and source choice.

| Arm | Total selections | Median | p95 | Worst | Single-character bits | Dictionary bytes | Complete package bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frozen original, 128/7 | 28,996 | 131 | 555 | 1,356 | 87.30% | 1,844 | 33,434 |
| Frozen normalized, 128/7 | 20,575 | 121.5 | 296 | 432 | 80.98% | 1,844 | 26,065 |
| Relearned input, 128/7 | 20,534 | 121 | 296 | 432 | 81.14% | 2,244 | 26,429 |
| Smaller storage, 127/7 | 20,688 | 122.5 | 296 | 432 | 81.07% | 1,677 | 25,996 |
| Frozen original, 256/8 | 22,097 | 82 | 537 | 1,272 | 77.11% | 3,292 | 31,539 |
| Frozen normalized, 256/8 | 13,194 | 78.5 | 225 | 309 | 61.46% | 3,292 | 22,636 |
| Relearned input, 256/8 | **12,790** | **77** | **205** | **309** | **60.43%** | 3,833 | 22,773 |
| Smaller storage, 255/8 | 13,264 | 79.5 | 225 | 309 | 61.01% | 3,064 | **22,478** |

All arms cover 150/150 and contain zero whole-program entries. The final 8-bit input candidate costs 102,320 payload bits plus 6,150 framing bytes, with zero padding. Dictionary and packets together cost 22,773 bytes. The 7-bit input candidate costs 143,738 payload bits, 542 padding bits and the same framing, totaling 26,429 bytes. Decoder/interpreter/tooling storage is separate; no model or cluster-selector is used. Human navigation/control inputs are not measured in this offline experiment.

| Input arm | Original 100 selections | Shared 125 selections | New 25 selections | Full 150 |
|---|---:|---:|---:|---:|
| Frozen normalized 128/7 | 11,489 | 16,099 | 4,476 | 20,575 |
| Relearned 128/7 | 11,533 | 16,101 | 4,433 | 20,534 |
| Frozen normalized 256/8 | 6,613 | 9,836 | 3,358 | 13,194 |
| Relearned 256/8 | 6,646 | 9,840 | 2,950 | 12,790 |

Thus the 8-bit relearning gain is 404 selections overall, with a four-selection regression on the shared 125 (33 on the original 100) and a 408-selection improvement on the new 25. Package size grows by 137 bytes relative to frozen normalized. This is a tradeoff, not an across-the-board win. The stored alternatives remain available.

The seven-bit search evaluates 184 legal moves; the eight-bit search evaluates 440. Both remain below the frozen 600 total score-probe cap per width including ranking. Wall time is 6.83 and 12.33 seconds respectively. Seven-bit search stops without an improving tested neighbor; eight-bit search reaches its two-round limit. Reused breadth-first traversal source and the now-counted tree constructor explain much of the gain. This limited local search is not a global optimum.

## M1 and next decision

M1 still requires at least 400 of 500 frozen problems, at most 256 entries, median at most 32, p95 at most 96, at most 10% single-character selection bits, and zero whole solutions, with the 128/7 comparison. No threshold changed. M1 permits fitting its known source corpus; it is not an unseen-generalization claim. A concrete 500-problem population with complete interface and scoring contracts still needs to be frozen before qualification. The protected 66-problem reservation remains unopened and is not available to fill that population.

A read-only inventory at corpus revision 1810 finds an upper bound of **363** distinct potentially eligible problems across completed JavaScript ledger entries, the qualified catalog and the current development set, after protected exclusions. That is 213 potential additions, subject to exact qualification/provenance checks, and at least 37 more JavaScript admissions are needed even to make 400 coverage possible. Recognition/corpus admission remains user-owned; this experiment does not create claims or change that ledger.

Increasing the set alone worsens aggregate compression. The next bounded independent step is better lexical/token-boundary proposal mining and deeper exact dictionary refinement on these same 150 programs. Separately, subsequent expansion can consume only already completed, qualified development material, with a new frozen stage and all failures retained. Admission and the explicit 500-problem population are milestone dependencies, not reasons to relabel this result as success.

## Preserved evidence

`stage-freeze.json` is immutable. Its inherited validation prose accidentally says “125 denominator”; the new stage IDs and all qualification/measurement records correctly use 150. This is a documented prose erratum, not a population change.

The initial source preparation and failed qualification remain at the stage root. `attempt-002/repair-contract.json` freezes explicit constructor accounting; `attempt-002/contract.json`, generated sources, observations and qualification report retain exact lineage. `measurement/` contains the dictionaries, full program sequences, decoded source and packet files; `summary.json` and `independent-audit.json` bind the results. Private sources, cases, dictionaries, sequences and native logs remain private. Public reporting includes only methods, IDs, hashes and aggregate measurements. No BITS vocabulary or deployment is changed by this experiment.

Public evidence links: [stage freeze](evidence/stage.json), [qualification](evidence/qualification.json), [matched results](evidence/results.json), [independent audit](evidence/audit.json), [search budget](evidence/search-contract.json), [runtime costs](evidence/runtime-costs.json).

The method directory preserves the executed final code and predecessor preparation method, including original task-local paths. These are provenance records, not a turnkey portable runner. Reproduction requires the hash-bound private inputs and declared preparation successors. Private sources, cases, dictionaries, sequences, decoded programs and raw observations are intentionally excluded. The generic helper metric `new_source_problems` was removed from the public aggregate because it counts variant-name prefixes, not new problem IDs; the frozen new-problem denominator is exactly 25.
