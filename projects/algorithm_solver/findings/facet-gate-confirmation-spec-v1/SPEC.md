# Commissioning spec: independent confirmation of the frozen 1b facet gate

## What this document is

It specifies how an independent author prepares, and how the team then scores, the confirmation set for the
frozen 1b candidate. It authors no cases, and nothing here is evaluated. claude wrote it, codex will review it, and
the owner approved the confirmation itself (2026-10-23, quoted below).

> "For recognition 1b, preserve the frozen fix and commission independently written cases covering ambiguity,
> abstention, and the two earlier wrong acceptances. Four correct answers with no errors is promising development
> evidence, but insufficient coverage for promotion."

## The frozen candidate (unchanged; do not modify)

The candidate is [facet-gate-dev-128-v4](../facet-gate-dev-128-v4/README.md) strict arm **S**, frozen at
`919dbc603` and recorded at `190832237`:

| Component | Identity |
| --- | --- |
| Gate | `algsolve/facet_gate.py`, SHA-256 `8e7ffec539cbe5fdbc1d69cfec44b55266ab376538dd42b1d791f40538f2ddde` |
| Contracts | `contracts/facet_gate_dev_128_v4_strict.json`, SHA-256 `e9b29759f90bffd1803bfefb6c279c2395ce47673d8f33a1613df786572b9f14` |
| Index | the retained 66-entry `recognition-rebuild-dev-suby-v1` |
| Approval catalog | its original catalog |
| Thresholds | unchanged |
| Encoder | the 128 encoder |
| Runtime | `runs/facet-gate-approval-runtime-128-v4` (96 approval bindings) |

The defaults ablation D is not under confirmation.

The confirmation run re-verifies every one of these hashes before inference. Any change to the gate, contracts,
grammar, thresholds or index after this spec is accepted makes the confirmation void for this candidate.

## Who authors and who reviews

- **Author.** One author who is neither claude nor codex, and who has not seen the gate code, the grammar, the facet
  contracts, the synthetic suite, the retained 24 development requests or the consumed fresh 36. A human author is
  preferred. If the owner instead approves an isolated agent role, it must start from a fresh context with only the
  materials listed below, and the record must say "agent-authored" rather than "human-authored".
- **Reviewer.** A second person or role, also independent of claude and codex. The reviewer checks labels, the
  hint-free wording and the category quotas. They may send cases back to the author for revision before sealing,
  but never after.

**What the author receives:**
- the 66 indexed source titles and keys, with their original statements;
- this spec's category table;
- the request format.

**What the author never receives:** anything from the candidate (code, grammar words, facet names or values),
anything from previous request sets, or any model output from the route.

## Population to write (counts are minimums)

| Category | Count | Content | Expected label |
| --- | ---: | --- | --- |
| C1 complete, reviewed sources | 38 | Two independently worded requests for each of the 19 reviewed sources (the 6 stock sources; kth largest and rank transform; house robber I and II; two-sum I and II; course schedule I and II; number of islands; max area of island; top-k frequent; minimum-size subarray sum; maximum subarray). Each fully specifies every answer-changing detail in the author's own words. | answer, with that source key |
| C2 materially ambiguous, reviewed families | 24 | Each omits or leaves undecidable exactly one answer-changing detail, so at least two readings with different correct outputs remain. At least 4 per row of the next table. | abstain (ambiguous) |
| C3 the two earlier wrong acceptances, re-authored | 12 | Six requests that state no trade-count or trade-optionality limit for a single-share stock problem, and six that leave the duplicate policy of a k-th largest request undetermined. All new wording; no text from the consumed fresh 36 or the retained 24. | abstain (ambiguous) |
| C4 indexed but unreviewed sources | 12 | Complete requests whose correct stored answer is one of the 47 unreviewed indexed sources. | answer is correct; abstention is allowed |
| C5 outside the index | 8 | Requests for well-defined problems not in the 66-entry index, including near neighbours of indexed families. | abstain (no stored answer) |

**C2 quotas (at least 4 cases each).** The author has to know these details exist to write the ambiguity, but
writes the wording independently.

| Family | Omitted detail |
| --- | --- |
| stock | trade count, or whether trading is optional |
| rank | duplicate policy |
| houses | circular versus linear street |
| islands | diagonal connectivity, or whether border-touching islands count |
| pairs and windows | one-based versus zero-based positions, or sorted input |
| courses or frequency | output form |

**Request format, per case:**
- the request text, a few sentences, informal and without solution hints, algorithm names or complexity
  requirements beyond the problem's own;
- the function interface;
- at least two public input/output examples.

For C2 and C3, the examples must be consistent with at least two of the materially different readings, so that
public checking cannot settle the ambiguity. The reviewer verifies this by computing each reading's outputs by
hand or with an independent reference.

**Per-case labels:** the category; the expected decision; for an answer, the expected source key; for C2 and C3,
the omitted detail and the competing readings.

Total: 94 or more requests.

## Protection and sealing

1. **Storage.** The author writes the cases outside the repository, in a directory that claude and codex cannot
   read, for example a protected owner path on Jupiter.
2. **Sealing.** After review, the reviewer computes the SHA-256 of the case packet and of the label file
   separately. The packet hash is committed to the repository as a seal. The labels stay with the reviewer until
   all decisions have been sealed.
3. **Running.** The scoring driver loads the packet, runs the frozen candidate S once, and the unchanged control
   route once, on every request. It writes all decisions, then seals them by hash **before** loading the labels.
   Real embedding and retrieval in alternating order, identical vectors and candidates per pair, and the 2 s
   route budget all follow facet-gate-dev-128-v4/compare_real.py.
4. **Scoring.** Only then are the labels loaded, and each accepted answer is checked:
   - expected source identity;
   - catalog approval;
   - the source's test suite;
   - the request's own public examples.
5. **No second pass.** No rerun, tuning, grammar or contract edit, or relabelling happens after the packet is
   opened. The opened set becomes consumed development data. It can never be reused as confirmation, and the
   result is recorded whatever it is.

## Pass rule (fixed before any case is written)

The candidate **passes** confirmation only if all of the following hold.

| | Condition |
| --- | --- |
| R1 | **No wrong acceptance** in any category. A wrong acceptance is an answer whose source identity is wrong, or whose code fails the source tests or the request's examples. |
| R2 | **Every C2 and C3 case abstains** (36 or more). This is the mandatory-ambiguity behavior that the consumed fresh 36 failed. |
| R3 | **Every C5 case abstains.** |
| R4 | **C1 coverage: at least 60% of the C1 requests are answered correctly**, at least 23 of 38. This is a proposed threshold. 1b has no agreed coverage gate, so the owner confirms or replaces this number before the packet is sealed, and the rule is frozen then. |
| R5 | No infrastructure error, unqualified answer or route-budget failure, and no drift in the control route. |

**Always reported, in addition to the pass decision:**
- the control route's results on the same cases;
- each category separately;
- the abstention reasons;
- C4 coverage;
- the exact (Clopper–Pearson) 95% upper bound on the wrong-acceptance rate.

For example, with no wrong acceptances in about 60 accepted answers, that bound is about 6%.

**Not claimed even if the candidate passes:**
- 1b qualification beyond this index;
- the historical full-catalog gate (18/20 with 4/4 absence);
- 1a gates;
- unseen solving;
- any relabelling of the consumed fresh 36.

A pass permits proposing promotion to the owner; it does not promote anything by itself.

## What the team prepares meanwhile (no case content)

- A sealed-packet loader and the scoring driver, as a copy of compare_real.py with packet and label hashes and a
  sealed-decision step. It is tested only on synthetic placeholder packets.
- A dry check that the runtime and all candidate hashes still verify.
