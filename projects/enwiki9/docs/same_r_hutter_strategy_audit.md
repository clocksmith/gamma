# SAME-R Hutter Strategy Audit

This audit maps Gamma's current SAME-R method to the enwiki9 prize program.
The canonical outer-method documents are
[`projects/samer/README.md`](../../samer/README.md),
[`CAUSAL_AND_EVIDENCE_CONTRACTS.md`](../../samer/CAUSAL_AND_EVIDENCE_CONTRACTS.md),
and [`SELECTOR_AND_SATURATION.md`](../../samer/SELECTOR_AND_SATURATION.md).

Claim boundary:

```text
SAME-R is an experiment and promotion method, not a compressor.
This audit does not prove an enwiki9 score.
Only an exact 1,000,000,000-byte result with roundtrip true and counted
official score <= 109,500,000 proves the target.
```

## Verdict

The project has the correct outer strategy and the right classes of inner
mechanism, but it does not yet have a constructive target-closing integration.
The strategy is therefore suitable for continuing the search, not evidence
that the prize has been won or is guaranteed.

The decisive design choice is correct: evaluate every proposed retrieval,
teacher, router, or mixer against exact FX2/cmix residual codelength after
counting code and table bytes. Semantic similarity, raw SRSTC gain, training
loss, and forecasts may select experiments but cannot promote a candidate.

## Evidence That Fixes The Search Direction

```text
calibrated full-score forecast             110,181,114
target                                     109,500,000
forecast debt                                  681,114
best raw SRSTC net shadow gain                 900,464
conditional raw-shadow score               109,280,650
unchanged SRSTC transfer to FX2 heldout              -4
unchanged SRSTC transfer after code              -16,080
```

The raw SRSTC signal is large enough in isolation, but the unchanged FX2
transfer failure proves that the candidate substrate and the intervention must
be evaluated together. The next useful mechanism must predict FX2 residuals,
create a new decoder-rebuilt expert/state representation, or change reversible
layout. Adding the raw shadow gain to the FX2 forecast is invalid.

The Qwen fixed32 selector lane is retained but removed from the promotion
queue. Its sampled truth-aware oracle is about `1,079` gross bytes per `1M`,
while the frozen screen requires `700`; existing causal students realize none
of that signal. This is insufficient demonstrated realizable margin, not a
disproof of teacher-guided discovery. A successor Qwen lane must create new
causal experts or state representations rather than select only the same weak
candidates.

## SAME-R Contract Coverage

| SAME-R requirement | Current enwiki9 mechanism | Status |
|---|---|---|
| One capability and external metric | Minimize exact counted enwiki9 score to `<= 109,500,000`. | Present. |
| Frozen baseline and population | Exact corpus scopes, candidate IDs, FX2 stored stream, probability traces, and block splits. | Present for existing screens. |
| Deterministic verifier | Arithmetic codelength, native archive bytes, roundtrip, determinism, RSS guard, and official accounting. | Present. |
| Causal decoder state | WRT/Wiki parser state, SRSTC prefix tables, cmix component outputs, and fixed-point online routing. | Present as mechanisms; target transfer remains unproven. |
| Payload economics | Code, static-table, state, program, and archive bytes are explicit gates. | Present; constructive accounting still required after integration. |
| Anchor, targeted, random control | Specified for Qwen-guided SRSTC in SAME-R. | Not yet executed as a complete matched trio on a viable candidate universe. |
| Negative-history retention | GEPA, sidecar, unchanged SRSTC-to-FX2, XML residual, and Qwen fixed32 failures remain receipt-visible and scope-limited. | Present. |
| Oracle economics before expensive search | Full-component and fixed-blend noncausal convex-hull ceilings gate the queued cmix/FX2 screens. | Implemented in the quarantined queue; awaiting proof-boundary execution. |
| Formal selector receipt | Operator priorities and controller receipts exist. | Partial; no shared SAME-R automatic selector claim is allowed. |
| Formal saturation | Candidate-universe oracle failures can retire exact mixer families. | Partial; no project-wide impossibility or saturation claim is allowed. |
| Native promotion ladder | Exact prefix -> 100M -> 1G -> official accounting, unchanged between passing gates. | Present. |

## Correct Mechanism Stack

The prize-facing stack should remain:

```text
strong reversible FX2/cmix substrate
-> exact residual/component traces on the identical transformed stream
-> noncausal oracle-economics ceiling for the frozen candidate universe
-> causal decoder-rebuilt expert or fixed-point router
-> untouched held-out block replay with all payload bytes charged
-> smallest paying native integration
-> unchanged exact prefix, 100M, and 1G proof ladder
-> official accounting and submission package
```

The inner mechanisms with credible byte leverage are:

1. `cmix21` component attribution to expose probability mass not already used
   by FX2.
2. SRSTC candidate generation over already-decoded typed spans, with explicit
   support, distance, copy length, and abstention.
3. WRT/Wiki causal state for title, prose, template, reference, URL, list,
   number, and section regimes.
4. Decoder-rebuilt token tries and typed copy channels for schema and rare
   continuation patterns.
5. Fixed-point regret, posterior, or fixed-share routing that predicts before
   observing the current truth bit and updates afterward.
6. Offline Qwen embedding/reranking only as a proposer of new compact causal
   features or experts under anchor, curated, and deterministic random-control
   lanes.

No mechanism is promoted because it is novel. It must first expose enough
gross residual signal, then realize positive held-out net bytes, and finally
survive native integration.

## Priority Order

1. Preserve and finish the unchanged guarded `100M` proof gate. Use only the
   terminal command emitted by `cmix21_gate_decider.py`.
2. At the proof boundary, run the pinned identical-stream cmix21 component
   trace and exact FX2 comparison.
3. If the full-component convex-hull upper bound is below `700` gross bytes per
   `1M`, skip the causal router and retire that exact component universe.
4. If the full bound passes, run the frozen causal router. Run the fixed-share
   replay only if its `80,000` ppm fixed-blend upper bound also passes.
5. Integrate only a causal held-out winner whose measured savings exceed code,
   table, and package cost. Do not extrapolate it into a score claim.
6. If the component universe saturates, generate new decoder-rebuilt experts:
   typed SRSTC candidates, WRT token tries, copy-distance/match-support experts,
   and residual-specific page regimes.
7. Use Qwen only after a new candidate universe clears a fresh oracle screen;
   then execute matched anchor, Qwen-curated, and deterministic random-control
   lanes with identical budgets and sealed blocks.
8. Promote the unchanged native package through exact larger scopes and
   official accounting.

## Retired Or Secondary Shapes

- Unchanged aggregate SRSTC correction over FX2 is retired; the concept is not.
- Qwen fixed32 selection over the current candidate universe is retired from
  promotion for insufficient realizable margin; teacher-guided new-expert
  discovery remains eligible.
- Generic embedding adjacency and page ordering do not answer the residual
  transfer question.
- Raw order-2 SRSTC savings are discovery evidence, not additive FX2 savings.
- Broad XML/SSE hashes, MWCC, and I-SSA remain diagnostic until they clear
  counted held-out economics.
- PPMD-only memory cuts are bracket evidence; the active proof package uses a
  different FXCM memory surface.

## What Would Confirm The Strategy Worked

The strategy first becomes capability evidence when a causal component beats
the exact base on untouched blocks after all code and table bytes. It becomes
constructive compression evidence only after native roundtrip and determinism.
It wins the stated target only when the full-corpus official receipt records:

```text
scope_bytes == 1,000,000,000
official_score_bytes <= 109,500,000
roundtrip_ok == true
```

Until then, the honest status is: correct search architecture, credible raw
signal, failed unchanged transfer, and one unresolved target-substrate
integration problem.
