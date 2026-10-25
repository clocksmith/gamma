# Fixed guard-v2 cached development evaluation

Prepared evaluator, **not yet executed**. Main reviews the exact `freeze.json`
before authorizing the bounded host run. This is not encoder or candidate work.

## Frozen comparison

- Preserve all 52 existing authorized development queries, exact order and labels.
  Labels enter scoring only; no grammar or threshold tuning occurs here.
- Preserve all 4,081 competitor IDs and the exact 54 enriched-document replacements.
  Cache receipts/arrays bind full document/query text, encoder identity, order,
  IDs, truncation metadata and SHA256 bytes. No query or document is re-encoded.
- Pin guard v2 freeze `4b534b02…cf5824`, code, its imported dependencies, original
  policy family, upstream cache identities, original historical result and the
  **same v8 service configuration** as the historical enriched comparison.
- Evaluate exactly the original 20 cosine/margin policies and unchanged selection
  criterion. No extra thresholds, score-based candidate availability filter,
  reranking, runner-up fallback, guard edit, confirmation read or source execution.
- Before any guard conclusions, reproduce every historical baseline decision's
  status, reason, identity and exact implementation selection, and baseline metrics.
  Tiny floating-point score rounding is not required to be bit-identical; the
  decisions and selections must match. Any mismatch fails closed.
- Enforce that each guarded acceptance was already accepted with the same exact
  identity and implementations by its corresponding unguarded policy.

The full query vector matrix and full competitor matrix are loaded once. The
original `rank`, `decide`, `score_decisions`, `select_policy` and frozen
`guarded_decide` are reused. The index restoration helper is code-pinned; it
imports no encoder. The guard's original per-ID pre-open boundary checks gate
all 54 semantic documents before extraction. The exact service is metadata-only
(`include_source=False` throughout). Other identities remain unknown competitors.

## Output and limits

`report.json` contains all 20 baseline/guard metric pairs, deltas, selected policy,
52 per-policy compact decisions, grammar/facet coverage, and actual processing
CPU/wall/RSS. Query text/spans, source bytes and full embeddings are not exported.
This is cached processing cost, **not fresh serving latency**. Four request timing
work elsewhere is a separate experiment.

Hard host limits: 512 MiB address space, 60 CPU seconds (59-second soft signal),
60 wall seconds, one BLAS thread. Failures write `failure.json` with phase/type;
no partial result is described as a completed evaluation. Model imports, downloads,
GPU use, candidate execution and confirmation access are absent.

This is the previously authored non-IID development cohort, not independent
confirmation, a population risk certificate or recognition qualification. A guard
can only veto under this composition; useful coverage and zero observed errors
still require honest reporting, not a generic applicability-proof claim.

## Focused synthetic verification

Eight owned synthetic tests cover cache/text/order identity, pin tamper,
52-row alignment, no raw-span export, baseline drift blocking, unchanged policy
count and veto-only identity/selection retention. No real vectors were loaded and
no cohort was scored by these tests.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. timeout 60s bash -c '
  ulimit -v 524288
  python -m unittest discover -s projects/algorithm_solver/catalogue/description-applicability-evaluation-v2 -p test_evaluate.py -v
'
```

After main's exact-freeze review only:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. OPENBLAS_NUM_THREADS=1 \
python projects/algorithm_solver/catalogue/description-applicability-evaluation-v2/evaluate.py \
  --freeze projects/algorithm_solver/catalogue/description-applicability-evaluation-v2/freeze.json \
  --freeze-sha256 REVIEWED_SHA256 --output NEW_PRIVATE_OUTPUT_DIRECTORY
```
