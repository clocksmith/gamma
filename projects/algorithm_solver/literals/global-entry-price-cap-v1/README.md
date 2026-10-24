# Global entry pricing

## Accepted invented measurement, 2026-10-24

The single [frozen measurement](SYNTHETIC-SPEC.md) passed. All20 registered
oracles and both original invented fixtures completed within the600-second
whole-process envelope. Final supervisor169.305032seconds, worker168.874491seconds,
oracles0.940598seconds and cleanup0.000175seconds. Peak worker893056KiB and
supervisor137468KiB are separate cumulative peaks, not a simultaneous total.
All64 code and12 runtime pins remained unchanged. See the byte-exact
[result](synthetic-results.json) and [supervisor](synthetic-supervisor.json).

| Invented fixture | Strict raw/integer budgets vs57 | k3 bound | Largest positive k | Full256 bound57 ->66 | Selected price |
| --- | ---: | ---: | ---: | ---: | ---: |
| Paired prefix75k | 172, k85–256 | 63143, unchanged | 81, unchanged | -57362 -> -2265 | 256000000 |
| Repeated owner12k | 251, k6–256 | 28459, unchanged | 4, unchanged | -151368 -> -13900 | 0 |

For paired75k the selected global charge is262531279050: entry charge65536000000
plus residual196995279050. Positive pricing improves the standalone unpriced
all-entry bound from-159066 to-2265. For repeated12k the winning zero-price
charge is245833750000, so its gain comes from the unpriced all-entry cap and
must not be attributed to positive pricing. Both fullcapacity bounds remain
negative; neither extends the positive budget range or proves10% unreachable.

Production/checker times were33.684940/74.212898seconds and20.019229/36.201673seconds.
These are phase measurements, not matched total-time ratios or corpus forecasts.
Full historical50/53/57 science, every57 and all15-price/unpriced forward recurrence,
global counts, exact work counters and all257 rows independently reconcile.
The intermediate worker-status file remains a last-progress snapshot; final
worker/result/supervisor receipts establish completion and no failure marker exists.

Root and a separate reviewer audited acceptance and metadata arithmetic without
rerunning kernels. Result SHA256:
`43826f2616230eee54eb5114e5353726a613a815bffc3572782fd43f621dccb8`.
No private input was opened. This is an invented-input result, not original-fit
performance, M1 qualification, a dictionary witness or a fullclass exclusion.
A new reviewed corpus design must explicitly reconstruct61 before combining
its same-q bound with the global cap. Existing measured files remain frozen.

## Historical theorem and supplied implementation stages

Item 66 proves a cardinality-aware charge across all fixed source paths.
For each allowed entry, divide a nonnegative integer price by its total
occurrence count across all sources, rounding down. Subtract that amount
from each occurrence penalty, clipping at zero. Each selected entry removes
at most one price globally, so a dictionary with at most B entries has
penalty at most `lambda*B + sum(residual path caps)`.

The [proof and scope](DRAFT.md), [tiny oracle](proof.py) and
[exhaustive checks](test_proof.py) keep source geometry, bans and paid entries
fixed. An explicit minimum with the same-q item57 charge preserves its bounds.
Zero price alone does not recover or universally dominate item57 or item63.

A coverable invented example gives charges 80 for item57, 60 for item60 and
52 at a positive global price. Its lower bound remains -58. Another example
attains a positive bound, but both use supplied general q, not corpus q53.
Neither establishes original-fit improvement or a full256 certificate.

Seven focused tests passed in 0.126 seconds; compile/import passed. Root and
an independent reviewer found no mathematical implementation blocker; see
[review](REVIEW.md). This is a theorem and tiny implementation record only.
No private inputs, scalable implementation, price tuning or measurement.
A separate reviewed scalable design and frozen protocol must precede either
an invented performance measurement or original-input execution. Component
intent and admission, qualification and publication boundaries are unchanged.

## Supplied scalable kernels

The [approved design](DRAFT-NEXT.md) now has supplied-input
[production](caps.py) and [independent checking](independent.py), with
[production tests](test_caps.py) and [checker tests](test_independent.py).
Counts cover every allowed shared and owner occurrence. The fixed15 prices
produce all-entry residual schedules, global entry charges and an explicit
minimum with57. Unpriced all-entry vectors remain distinct from57's owner caps.

Eight production checks passed0.177seconds and five independent checks
passed0.281seconds, including actualq53 tiny oracles, real JSON transport at
B0/1/16/256 and all supplied recurrence/count/cap comparisons. Root and an
independent reviewer found no blocker. There is no invented performance or
original-input measurement yet, and no61 combination is silently included.

## Original-input continuation prepared

The [new design](DRAFT-CORPUS.md) and [execution freeze](FREEZE.md) explicitly
combine the measured global cap with freshly reconstructed56 coverage and61
required-owner allocation. The original nine files remain the only input set.
All measured code is unchanged; every baseline/global/coverage recurrence and
all257 combined rows must reconcile in fresh independent reporting.

Twenty binding/lifecycle checks and nine invented integration checks pass;
see [review](REVIEW.md). This is prelaunch preparation, with no original66
input opened and no corpus result. A pushed exact pending inventory, Claude
cross-review and exact activation precede execution. The29 focused checks do
not establish original-fit acceptance, performance or M1 qualification.


## 2026-10-24 original-fit result: no gain over required-owner bound

The [frozen original-nine run](FREEZE.md) and independent replay both accepted.
The combined min(T61,G) exactly equals61 at every defined budget in both
cohorts. The global bound never wins or ties: required-owner is active at all
254 defined budgets per cohort. Budgets0–2 remain empty/null.

| Cohort | Combined k3 | Largest positive k | Combined k256 | Standalone global bound |
| --- | ---: | ---: | ---: | ---: |
| R | 13349 | 9 | -26872 | -43319 |
| naming | 6011 | 4 | -27652 | -43955 |

Both global minimizers are uniquely index8, lambda128000000. R global charge
136854529835 splits into32768000000 entry charge and104086529835 residual;
naming122011140578 splits into32768000000 and89243140578. Positive pricing
improves standalone unpriced bounds by23386/20252 integer units, yet remains
weaker than61 everywhere. Neither interior selection nor this null establishes
grid adequacy, impossibility of a better certificate, or an attainable10% witness.
The large-budget63 bounds remain stronger than this66 headline.

P1 is true; P2–P5 are false. All original28/50/53/57 commitments, fresh56/61
coverage/allocation, global multiplicities, every baseline/unpriced/15-price
numeric and Boolean recurrence, and all257 rows were independently reconciled.
The fixed global family adds no original-fit support exclusion beyond61's
at-most9 one-owner entries for R and4 for naming. Item59 establishes those
classes are nonempty; full256 remains inconclusive.

Production/report supervisor times were74.126217/131.616489seconds, both with
strict integer exit codes[0,0]. Result collection clocks73.511096/119.787420
are distinct from supervisor envelopes. Production workers took61.462078 and
71.723893seconds; independent workers115.553280 and119.206804seconds. Their
peak RSS values were577248/561612KiB and1138168/1117772KiB respectively,
separate process peaks. Cleanup took0.000115/0.000129seconds. All134 code,
23 runtime and33 public pins remained unchanged.

See byte-exact [results](evidence/results.json), [report](evidence/REPORT.md),
[production supervisor](evidence/production-supervisor.json) and
[report supervisor](evidence/report-supervisor.json). Result SHA256:
`e48231b33ee34aa90111c08254eed30a18ba64e5336cfe015c73dd660f637625`.
Root and a separate reviewer checked receipts, hashes, every public row and
price-component arithmetic without rerunning kernels. No dictionary, source,
qualification, validation, protected, M1 or current-best change. Component
intent and publication/admission boundaries remain preserved.
