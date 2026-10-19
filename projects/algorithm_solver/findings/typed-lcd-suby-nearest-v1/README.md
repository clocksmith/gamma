# Local nearest-compatible-fit-graph baseline

The separately named `typed-lcd-suby-nearest-v1` baseline returned **2/10 correct
fit answers and 0/8 correct audit answers**, with zero wrong acceptances and zero
infrastructure failures. Sixteen requests abstained. This is a completed negative
development baseline, not learned composition or evidence of arbitrary unseen
solving. [Aggregate receipt](summary.json) and [pre-inference contract](contract.json)
retain fixed identities, reasons, budgets and source hashes.

The baseline uses the [newly qualified local corpus](../typed-lcd-suby-development-v1/README.md):
15 fit graphs across ten fitting problems, plus eight audit problems, all previously
examined development. Requests passed to the route contain public input fields
only; audit teacher graphs and independent outputs are absent. Fit graph
representations and query inputs use the same approved Qwen encoder/instruction
as the existing typed pipeline. Select by embedding similarity among compatible
public signatures; alpha-rename positions only. No graph, literal or algorithm
edits, training, generator or test-driven search occurs.

Every public decision was saved before source-authority independent scoring.
The two-second complete decision budget stayed unchanged. Expected outputs remain
host-only in the existing isolated judge. Complete decisions, final graphs/code,
public errors and independent failures remain local and ignored.

| Partition | Correct accepted | Wrong accepted | Abstained | Complete p50 / p95 / max |
|---|---:|---:|---:|---|
| Fit (10) | 2 | 0 | 8 | 4.027 / 6.706 / 6.981 s |
| Audit (8) | 0 | 0 | 8 | 1.988 / 2.680 / 2.846 s |

Fit reasons: seven decision-budget failures, one public failure, two returned
answers. Nine fit programs passed independent source checks, including seven
that abstained under the budget; those seven are not returned-correct answers.
Audit reasons: four budget failures, two public failures and two unsupported
compatible interfaces. No audit program passed independent checks.

The main measured cost is query embedding/retrieval: median 4.014 seconds on fit
and 1.982 seconds on audit, compared with roughly 0.005 seconds construction.
A new prediction head alone does not establish that the full route meets the
existing latency gate. Preserve this measurement; do not relax the gate or
reinterpret repeated-input caching as fresh-query latency.

The full baseline took **136.90 seconds wall**, **442.02 process CPU seconds**,
**3,395,506,176 bytes sampled peak aggregate RSS**, and **1,305,555,736 bytes**
across monitored asset/run roots, within four CPU threads, 8 GiB RAM, 5 GiB disk
and the 900-second cap. Encoder loading/hash verification took 4.183 seconds;
15 fit-graph embeddings took 68.433 seconds setup, separate from request timings.
The host was shared. Source-private scoring is outside the complete request
budget and inside total experiment wall time.

Twenty-three focused baseline/comparison/scoring tests and 13 subtests passed.
These are separate from real program execution. The additional proposed-training
input/idempotence checks passed ten tests and 24 subtests without a fitting run.
Neither software checks nor label qualification qualifies a composer. The
standalone baseline source contract predates subsequent new preparation modules;
strict full-source-set resumption rejects a changed repository rather than
silently relabeling old evidence. All originally bound source bytes and the
completed artifacts remain preserved. A future matched run must freeze its own
complete final source identity before inference.

Next: under the exact newly named training resource scope, produce a fit-only
predictor, then seal one matched raw/constrained/nearest comparison with the
existing correction and correctness-selection rules. Preserve this standalone
baseline and its budget failures. Historical reproduction stays blocked; no
protected composition or nearby-variant scoring has run, and the autonomous
learning loop remains deferred.
