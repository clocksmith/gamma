# Share counted matrix traversal fragments

Four coordinated source rewrites reduce the same 100-program eight-bit baseline
from **6,938 to 6,613 selections (4.68%)**, median **58.5 to 57**, with **256 entries**.
Package size grows **25 bytes**, p95 stays **148**, and character fallback only
moves from **53.272% to 53.198%**. These are offline representation results; M1
and autonomous assembly remain unqualified.

## Matched controls

The baseline includes the prior qualified window rewrite; its gain is not counted twice.

| Eight-bit arm | Selections | Dictionary B | Packet B | Package B |
|---|---:|---:|---:|---:|
| Baseline | 6,938 | 2,942 | 11,038 | 13,980 |
| Source-only | 6,932 | 2,942 | 11,032 | 13,974 |
| Six-entry deletion control | 6,968 | 2,800 | 11,068 | 13,868 |
| Dictionary-only | 6,968 | 3,292 | 11,068 | 14,360 |
| Joint, selection objective | **6,613** | 3,292 | 10,713 | 14,005 |
| Joint, storage objective | 6,962 | 2,800 | 11,062 | **13,862** |

At seven bits, selections improve **11,549 to 11,489** and median **102.5 to 95.5**,
but p95 worsens **250 to 251**, worst **394 to 399**, character bits **76.942% to
78.492%**, and package **15,742 to 16,040 bytes**. The storage alternative instead
uses the original dictionary with one new source: 11,520 selections / 15,716 bytes.

## Mechanism and costs

Spiral traversal and generation (#54/#59) share coordinate visitation; histogram
and maximal-rectangle problems (#84/#85) share monotonic-stack visitation. Callers
compute distinct outputs. Three exact strings encode the spiral helper, two the
stack helper, and one a repeated area callback. Every fragment is reused by two
selected problems. There is no whole-solution or whole-helper entry, problem-ID
dispatch, free source substitution, uncounted helper injection or model.

At eight bits the four costs change 128→33, 153→56, 81→11 and 144→51. Their
355-selection gain costs 30 selections elsewhere through displaced dictionary
entries: net 325. The corresponding seven-bit gain is 525 locally but 465 is
lost elsewhere. All collateral costs remain in the denominator.

The six additions contain 468 UTF-8 content bytes plus 24 length bytes. Replacing
six existing entries grows the eight-bit dictionary by 350 bytes. The winning
52,904 payload bits plus 4,100 framing bytes and 3,292 dictionary bytes total
14,005 bytes. Seven-bit padding is also charged. Decoder/runtime and offline
metadata are separate from this matched dictionary-plus-packet metric; no human
control/navigation or autonomous selection cost is claimed. Algorithmic time
and auxiliary-space classes are retained, but callback overhead is unmeasured.

## Bounded search and verification

The first pass had no free non-character slots: 126 nonempty subsets were rejected
at the cap, and only two empty subsets were evaluated. That negative result is
preserved. A separately frozen replacement pass ranks six successive removals
by exact complete-corpus loss, then tests all 64 declared-fragment subsets per
width. The unchanged source-only state remains eligible. It measured 1,122 deletion
probes and 128 subset probes in 15.85 seconds. All dictionaries obey the cap.
Removal choice is greedy; the restricted subset search is not global optimality.

Eight original/rewritten sources pass **4,584 native checks on 2,292 distinct cases**.
Independent oracles use turning walks, exhaustive histogram intervals and row-pair
rectangle scans. Tests include input/alias preservation, exact order and numerical
outputs, 100,000-element histograms and a 200×200 matrix. Expectations stay outside
the sandbox. Qualification takes 20.33 seconds with one worker.

Across both passes, **2,800 packets** independently decode and pass forward
segmentation and complete-cost audits. All **12 deletion steps** independently
replay; **400 final source choices** independently match among 680 alternatives;
692 observation files match receipt hashes. The remaining 96 problems retain
existing hash-bound native qualification, not newly rerun execution claims.

[Contract](evidence/contract.json) · [Replacement contract](evidence/reselection-contract.json) ·
[Initial result](evidence/initial-result.json) · [Replacement result](evidence/reselection.json) ·
[Qualification](evidence/qualification.json) · [Packet audit](evidence/packet-audit.json) ·
[Choice audit](evidence/choice-audit.json) · [Fragment identities](evidence/fragment-identities.json)

The method directory preserves exact executed code and original local paths.
Private proposals, source versions, expectations, dictionaries and packets are
not included. Reproduction requires those hash-bound local inputs. No protected
holdout, recognition ledger, BITS deployment or private Git ancestry is published.
M1 still needs 400/500 frozen problems, median ≤32, p95 ≤96 and character bits ≤10%.
