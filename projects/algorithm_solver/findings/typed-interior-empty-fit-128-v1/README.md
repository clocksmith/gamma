# Interior-empty-slot correction: fit-only captured-prediction replay

The smallest supported repair change improves structural validity without
improving solving. On the original ten fit captures, existing correction produced
nine valid graphs and four accepted-correct answers; the opt-in correction produced
ten valid graphs and the same four accepted-correct answers. Both abstained six
times and had zero wrong acceptances. No promotion or protected opening follows.

| Route | Valid /10 | Accepted correct /10 | Wrong accepted | Abstentions |
|---|---:|---:|---:|---:|
| Original raw prediction, retained | 8 | 4 | 0 | 6 |
| Existing correction, matched replay | 9 | 4 | 0 | 6 |
| Interior-slot correction, matched replay | 10 | 4 | 0 | 6 |

## Observed defect and bounded change

[Original invalid-graph diagnosis](invalid-graph-diagnosis.json) preserves raw
hashes and validator failures. Six of the ten original invalid graphs had
interior EMPTY slots (one fit, five audit); two failed expression shape, one
tree-edge validity and one statement shape. Audit inspection is diagnosis of
already consumed historical results, not a fresh audit test or selection.

The old repair pool considers non-empty op slots and one frontier at the count of
non-empty slots. A missing node inside the active prefix can be in neither set.
For fit case `lcd:1464`, slot 15 is empty while later slots remain active. Its
repair could never be proposed by the old pool. The opt-in
`include_interior_empty: true` adds those interior slots to op-edit eligibility.
It preserves model-ranked alternatives, penalty ordering, strict validation,
all literals, raw captures, maximum 64 edit options, maximum two edits,
maximum 128 attempts and the 0.2 s repair cap. Default behavior is unchanged.

The change repaired slot 15 from EMPTY to the model-ranked `pure:mul` in six
attempts, versus 128 unsuccessful attempts in control. The resulting graph failed
public examples, so the route correctly abstained. Repair cost on this case was
13.792 ms candidate versus124.794 ms control. Total repair costs across ten cases
were 45.217 ms and 150.738 ms respectively. Costs are measured on the active host and
do not claim stable speedup across runs.

## Evidence and limits

[Frozen candidate](candidate.json), [summary](summary.json),
[receipt hashes](integrity.json), [replay driver](replay_interior.py).
Raw decisions, graph programs and test results remain ignored under
`runs/typed-interior-empty-fit-128-v1/`.

All original capture, decision and scoring files remain unchanged. The replay
uses exact original codes/logits and codec, with no inference, training, nearest
answer substitution or query-time autoregressive generation. The only changed
configuration is interior op-slot eligibility. The ten fit decisions for both
arms were sealed before loading and hash-checking their original qualified
independent development suites. Scoring used the real Linux sandbox. Audit cases
were not rerun under this change, and protected cases were not opened.

Repair, assembly and execution costs are freshly measured. The original shared
inference durations are inherited only for applying the original two-second
decision budget. Reported hybrid totals are **not** a new end-to-end inference
measurement. New inference would need its own separately named matched run.

Focused verification: 12 tests and three subtests pass, including a synthetic
interior-hole regression proving default behavior is retained and the opt-in
candidate can repair without modifying raw codes or literals. These software
checks are separate from the ten-case executable result above.

This closes a specific search-eligibility defect, but validity is not correctness.
The remaining semantic failure stays recorded. Neither goals 2a/2b nor the
autonomous development-loop gate is qualified. Further construction changes need
a separate hypothesis and frozen diagnostic; do not retune this candidate's
literal or search budgets on its scored result.
