# Contradiction-only recognition: matched development comparison

The separately frozen `recognition-requirements-dev-suby-v1` candidate returned
**11/16 correct specified answers versus 7/16 for the unchanged reconstruction
control**. It retained every control success, added four correct answers and
introduced zero wrong or unqualified acceptances and zero infrastructure errors.
This passes the predeclared development-retention rule. It is consumed development
evidence, not a release, new holdout, generalization or learned-composition result.

[Aggregate receipt](summary.json), [pre-inference candidate seal](candidate.json),
[frozen reporting/selection contract](../../contracts/recognition_requirements_dev_suby_v1.json),
[deterministic checks](checks.json) and [development check history](development-checks-history.json)
retain the identities, outcomes, repairs and costs. Candidate SHA256:
`11e940fdca16abb0b968bd2459ff60285ed442f77e6c6a1bede9502296f69cfa`.
The [original control](../recognition-rebuild-dev-suby-v1/README.md) remains
`64f10768b5004782cf8549215357d8d08ee2be8cd74b8b6198fe8c7ced83a33e`.

## Matched result

Both arms received the same 66 indexed sources, cached source vectors, 24 request
objects and unchanged 16-source approval manifest. Query parsing received only
request text. No target identity, source statement, oracle signature or independent
output entered selection. The unchanged control reproduced all original
acceptance/abstention reasons, retained candidate orders and scores exactly.

| Population | Arm | Correct accepted | Wrong / unqualified accepted | Abstentions |
|---|---|---:|---:|---:|
| 16 specified requests | Control | 7 | 0 / 0 | 9 |
| 16 specified requests | Candidate | 11 | 0 / 0 | 5 |
| All 24 requests | Control | 7 | 0 / 0 | 17 |
| All 24 requests | Candidate | 11 | 0 / 0 | 13 |

The four useful changes are `pair-unsorted`, `houses-line`, `houses-ring` and
`stock-rest`. Explicit request facts excluded the conflicting stored contract;
unchanged confidence, sibling, source-approval and public-execution gates then
accepted the intended source. All 48 public decisions were sealed before
independent source-suite scoring. The seven control returns passed 557 source
cases; the eleven candidate returns passed 984. These are finite imported source
test agreements, not semantic equivalence or newly authored query-test evidence.
All eight no-example controls stopped before retrieval and remain **pre-retrieval
gate results**, not semantic absence or ambiguity detection.

## Mechanism and retained failures

The opt-in lookup adapter uses the existing explicit development grammar with
additional conservative suppression of negated, uncertain, alternative or quoted
contexts. Source facts are unchanged curated metadata bound by exact statement
SHA256; 22 of the 66 entries have bound profiles. The policy excludes only explicit
contradictions, keeps unknown and unapproved sources visible, and preserves
original scores and relative order. It does not infer a default from silence.
A generic source permitting arbitrary ordering is not excluded for sorted input.
The unchanged answer route repeats interface filtering on the candidate subset;
that small extra cost is measured. Production/default lookup is unchanged.

Five specified abstentions remain, preserved without retuning:

| Request | Retained failure |
|---|---|
| stock-once | The conservative alternative-clause guard suppresses the transaction fact in the sentence containing “or do nothing.” Unlimited trades remains first; its public check fails 1/2 and the route abstains. This is a parser limitation, not genuine user ambiguity. |
| stock-fee | Correct source remains below the unchanged score floor, 0.627357. |
| courses-order | Correct source remains below the unchanged score floor, 0.622252. |
| ranked-value | Correct source remains below the unchanged score floor, 0.510923. |
| islands-area | The square-output contract is excluded, but an unknown/unapproved closed-islands source remains ahead of the target. Its 0.000713 gap to the next candidate fails the unchanged general margin before approval/execution. No no-flip fact is invented. |

No failed qualification or public check was skipped to try a later candidate.
Public and independent infrastructure errors retain `sandbox_error` evidence.
No additional source was qualified, no profile or threshold changed, and no new
model/dataset/dependency was downloaded or trained.

## Measured cost and recovery

The comparison completed in **20.94 seconds monitored wall time**, with **53.10
process CPU seconds** plus **0.065 waited-child CPU seconds**, four CPU cores and
threads, **3,122,245,632 bytes sampled peak aggregate RSS** and
**1,299,532,056 bytes** across asset/control/new-run roots. The 8 GiB RAM, 5 GiB disk
and 900-second first-run caps were satisfied; no resource failure occurred.

The source index used 66 cached vectors; its historical embedding and source
qualification costs were not remeasured. There were **16 fresh query embeddings**,
shared identically between arms. Shared query embedding/retrieval took 10.784
seconds and was charged to each arm. Encoder load/hash verification took 4.328
seconds separately. Measured replay-arm totals were 0.505 seconds control and
0.684 seconds candidate, including public execution. Independent post-decision
scoring took 0.232/0.367 seconds. Actual paired-request wall totaled 17.266 seconds,
including first-request model setup and both arms; overall monitored wall also
includes startup, input validation, guards and scoring. The raw log remains local.

| Specified-request latency | Control | Candidate |
|---|---:|---:|
| Charged route p50 | 0.635 s | 0.638 s |
| Charged route p95 | 0.991 s | 1.018 s |
| Charged route maximum | 1.920 s | 1.955 s |

Charged latency adds the same measured shared retrieval to each measured replay
arm; replay itself is not fresh inference. The first forward remains included;
encoder loading and independent scoring are separate. No exclusive-host,
cold-machine or full-service latency claim follows from these measurements.

Fifty focused software tests and 39 subtests passed. Synthetic opposite,
paraphrase, missing/conflicting/negated facts, source-hash drift, unknown/unapproved
sources, immutable scores, numeric/sibling gates, exact lookup, public-failure
abstention and interrupted per-arm scoring recovery were checked. Four changed
Python files compiled and both new modules imported. These deterministic fixtures
are development checks, not independent confirmation. The check history retains
the initial system-Python dependency error and corrected synthetic-fixture error.

Completed-run resumption verified **149 new-run files and all 208 original-control
files**, preserving contents and mtimes with no repeated inference or judging.
Shared vectors and retrieval publish in one atomic receipt; each scored arm has
its own atomic receipt, so interruption does not replay completed judging.
Raw source, model, tests and code-bearing responses remain ignored and local;
only metadata and aggregate evidence are published here.

## Next boundary

Retain this separately named candidate for further development; no default route
or release gate was promoted. This frozen experiment is complete and must not be
retuned on these outcomes. The remaining parser loss, absolute-score limitations
and island contract coverage require a separately declared next candidate before
more inference. Fresh confirmation would need an agreed independent cohort and
existing release rules. Original composition checkpoint/corpus recovery and the
historical complete recognition index remain unresolved; this run supplies no
composer replacement and opens no protected evaluation. Gamma's recognition and
composition intent and authority boundaries are preserved.

Reproduce locally with the approved repository interpreter and offline assets:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.compare_requirements run
```

An existing completed run only verifies identity and returns its stored summary.
Do not remove the seal or use this command as permission to rerun/tune the cohort.
