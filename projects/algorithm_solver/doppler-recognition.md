# Doppler recognition for 1a / 1b

Gamma can now execute Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B through
Doppler's local WebGPU API. `algsolve.doppler_lookup` retains a Node process and
its model handles across JSONL requests. Python still owns retrieval, confidence
gates, stored-source approval and public-example judging. No query-time source
generation, downloads, automatic CPU fallback or clarification questions.

This is a separate recognition candidate. The existing qualified CPU command,
its catalog, thresholds and receipts are unchanged. The editor bridge has not
been switched to this candidate.

## Run

### Node and browser execution (2026-10-26)

`DopplerRuntime(..., surface='node'|'browser')` and the lookup CLI's
`--surface node|browser` use the same `doppler_session.mjs` operations. The browser
worker retains a headless Chrome instance and both model handles; model inference
executes in browser WebGPU, while Python retains retrieval and answer gates.
The shared ES module also accepts a browser caller's pinned `loadModel` callback.
Both paths check embedding token identity, finite normalized vectors, and complete
document-bound reranker scores. Runtime identity includes the surface and shared
module hash: previous index/calibration receipts cannot silently authorize this
successor. Build and calibrate a separately identified index for each surface.

The browser worker requires provisioned models inside the Doppler checkout,
Chrome, and Doppler's installed Playwright. Its HTTP server binds only loopback
and external requests are blocked. No model download or CPU fallback occurs.

Run the bounded physical integration probe with an interpreter containing NumPy:

```sh
systemd-run --user --scope --quiet -p MemoryMax=12G \
  timeout --kill-after=5s 240s env PYTHONPATH=projects/algorithm_solver \
  python3 -m algsolve.doppler_probe \
  --doppler-root /home/x/deco/doppler \
  --embedding-model /home/x/deco/doppler/models/local/qwen-3-embedding-0-6b-q4k-ehf16-af32 \
  --reranker-model /home/x/deco/doppler/models/local/qwen-3-reranker-0-6b-f16-af32 \
  --output /tmp/gamma-node-browser-probe.json
```

This uses the provisioned Q4_K embedder and F16 reranker with manifest execution
defaults. It checks physical execution, model switching, and Node/browser parity
on three synthetic cases. It does **not** establish catalogue precision/recall.
The owner's current target is at least 99% precision and at least 99% recall,
separately on each surface. Wrong positive and control acceptances count against
precision; positive abstentions count against recall. Missing cases, partial
indexes, development fitting and exact-ID bypasses cannot establish that target
for informal recognition. The synchronized authored imports are not automatic
qualification; use the current pinned catalogue and permitted documents, then a
fresh independent confirmation cohort. Preserve the consumed failed confirmation.

The [physical receipt](findings/doppler-node-browser-v1/physical-probe.json)
records identical Node/browser embeddings and reranker scores on Jupiter's Radeon
8060S for those probes, including an embedding repeated after reranking. Thirty
focused Python tests and four shared-session Node tests passed. The complete-cohort
scorer is `catalogue.recognition_acceptance.evaluate`; it rejects missing/extra
decisions and reports precision, recall, their denominators and Wilson intervals
without treating a point-estimate pass as release qualification.

The synchronized main at `a35e0a6c2` includes 192 additional authored pairs and
receipts for an earlier 502-JavaScript/503-Python qualified inventory (v22; later
adoptions are separate). It does not contain the current private catalogue,
boundary bundle, or full permitted recognition documents referenced under Dot's
`/workspace/shared`. Jupiter has none of those paths and Dot's registered SSH
hostname did not resolve during this work. Current population-wide accuracy is
therefore unmeasured for this Node/browser successor. Supply those exact pinned
artifacts and a fresh independently authored confirmation population before
claiming the requested 99% precision and recall. No protected data or consumed
confirmation queries were opened by this integration.

### Earlier reference-index candidate

Run from Gamma. Use provisioned model directories and the adjacent Doppler
checkout; no model installation is performed.

```sh
export PYTHONPATH=projects/algorithm_solver
DOPPLER_ROOT=/Users/xyz/deco/doppler
LANE=projects/algorithm_solver
```

The current local candidate reuses the original hash-pinned **reference document
embeddings**, computed by Transformers. New query embeddings execute in Doppler
with Q4_K weights. This mixed pair is explicit in the index contract and receives
its own development calibration. It does not claim that Doppler computed those
cached document vectors.

```sh
.venv/bin/python -m algsolve.doppler_lookup build \
  --doppler-root "$DOPPLER_ROOT" \
  --embedding-model "$DOPPLER_ROOT/models/local/qwen-3-embedding-0-6b-q4k-ehf16-af32" \
  --runtime-config "$LANE/contracts/doppler_recognition_runtime_v1.json" \
  --entries "$LANE/runs/web-solver-W002/inputs/corpus_entries.jsonl" \
  --catalog "$LANE/runs/web-solver-W002/inputs/approved-library.json" \
  --reference-vectors "$LANE/runs/web-solver-W002/inputs/corpus_embeddings.npy" \
  --reference-keys "$LANE/runs/web-solver-W002/inputs/corpus_embedding_keys.json" \
  --index "$LANE/runs/doppler-recognition-reference-v3"
```

Omit both reference options to compute document vectors in Doppler, using a new
output directory. Complete and partial indexes bind source hashes, ordered keys,
model manifests, execution configuration and worker identity; changed inputs
require a new directory. Protected composition aliases are excluded.

The checked-in runtime configuration uses Doppler's existing head128 prefill
attention and retained Q4_K materialization settings. It changes no model weights
or Doppler kernels. Hardware and output receipts remain separately scoped.

Calibration uses the existing consumed development descriptions. Historical
`clarify` labels mean **abstain**, never a question:

```sh
.venv/bin/python -m algsolve.doppler_lookup calibrate \
  --doppler-root "$DOPPLER_ROOT" \
  --embedding-model "$DOPPLER_ROOT/models/local/qwen-3-embedding-0-6b-q4k-ehf16-af32" \
  --reranker-model "$DOPPLER_ROOT/models/local/qwen-3-reranker-0-6b-q4k-ehf16-af32" \
  --runtime-config "$LANE/contracts/doppler_recognition_runtime_v1.json" \
  --index "$LANE/runs/doppler-recognition-reference-v3" \
  --development "$LANE/contracts/natural_description_dev_v1.json" \
  --output "$LANE/runs/doppler-recognition-embedding-dev-v3"
```

Add `--rerank` and choose a separate output directory to fit the reranked route.
The reranker model path alone does not enable reranking. Retain the same model
configuration when using a saved calibration.

For requests, use `query` with the same runtime/index flags, plus `--catalog`
and `--calibration .../calibration.json`. Supply `--queries requests.jsonl`, or
leave it out and send one [Problem packet](editor-protocol.md) per stdin line.
Keep the process open to retain model residency. Enable `--rerank` only with its
matching calibration. Responses are one JSON object per line.

Without calibration, the route returns candidates and abstains. With calibration,
it still checks exact stored-source approval, sibling identity, confidence,
interface compatibility and the query's public examples. Missing examples or
Linux sandbox availability fails closed. Returned answers carry
`recognition_qualified: false`: development fitting does not establish release
accuracy. Exact statement/interface matches avoid unnecessary model calls.

## Verification and limits

### Paired scoring-policy diagnostic

`algsolve.rerank_policy_comparison` compares `true_logit` and
`logit_difference` from one execution of each query/document pair. It retains
both logits, executed token IDs, candidate identities and runtime receipts;
neither the model manifest nor serving thresholds are changed. Candidates are
sent in chunks of at most ten, supporting fixed development shortlists of up to
50 documents. This is pairwise scoring, not a listwise model call.

Run from Gamma with provisioned models and explicit resource limits:

```sh
systemd-run --user --scope --quiet -p MemoryMax=12G \
  timeout --kill-after=5s 240s env PYTHONPATH=projects/algorithm_solver \
  .venv/bin/python -m algsolve.rerank_policy_comparison \
  --synthetic --surface node \
  --doppler-root /home/x/deco/doppler \
  --embedding-model /home/x/deco/doppler/models/local/qwen-3-embedding-0-6b-q4k-ehf16-af32 \
  --reranker-model /home/x/deco/doppler/models/local/qwen-3-reranker-0-6b-f16-af32 \
  --output projects/algorithm_solver/runs/rerank-policy-node-new
```

Use `--surface browser` and a separate output directory for browser execution.
`--synthetic` uses the three existing integration probes. Alternatively,
`--cohort permitted-development.json --review independent-review.json` accepts
this explicit input shape:

```json
{
  "schema": "gamma.rerank-policy-input.v1",
  "partition": "development",
  "cases": [{
    "id": "query-1",
    "query": "Return indices of two array elements summing to a target.",
    "target": "pair-indices",
    "documents": [
      {"key": "pair-indices", "text": "Return two indices whose values sum to the target."},
      {"key": "pair-values", "text": "Return the two values whose sum equals the target."}
    ]
  }]
}
```

Only supply already permitted development text. The CLI does not resolve
catalogue IDs, authorize protected text, or open an evaluation population.
Custom cohorts require an independently produced review with schema
`gamma.rerank-confusion-review.v1`, `approved: true`, an empty `blockers` list,
and `cohort_sha256` equal to the canonical `digest(cohort)` from the comparison
module. The run binds the complete review and its file hash. This identity check
preserves a review decision; a self-authored approval is not independent review.
Use a null target for unmatched/ambiguous controls; a positive target absent
from its shortlist remains in the recall denominator. Candidate identities
and all queries must be retained. The input supports at most 100 queries and
4 MiB, with a 500 KB per-query packet bound.

`contract.json` freezes inputs, runtime and comparison code before inference.
`observations.jsonl` retains each completed query; interrupted runs retain
their partial evidence without a completed summary. `summary.json` fits
separate thresholds for each policy on the same development cohort. Those
figures are in-sample diagnostics, not held-out accuracy, calibrated production
probabilities, or recognition qualification. Execution timing is shared by the
two derived policies; it cannot establish a policy-specific inference speedup.
For reproducible replay, use the pinned code and call `summarize` on the frozen
cohort and observations; do not mix a successor cohort with earlier logits.

The adapter verifies request IDs/hashes, finite normalized vectors, original
candidate ordering, manifest identity and the exact embedding tokens executed.
Timeouts and malformed results close the worker. Logs remain under
`runs/doppler-runtime/session-*`; no generated replacement answers are used.

The first integration passed token arrays as prompt text. That produced finite
but semantically invalid vectors. Its `doppler-recognition-m3-v1` index and
`doppler-recognition-embedding-dev-v1` failure are retained. The corrected worker
passes text plus explicit `inputIds` and rejects token disagreement. A focused
Node boundary test protects that call contract.

`doppler-recognition-m3-v2` retains a partial corrected, fully recomputed index.
The active reference-v3 candidate pins the existing document matrix instead.
Neither failed nor partial index is an approved serving index.

Focused tests:

```sh
PYTHONPATH=projects/algorithm_solver:projects/algorithm_solver/tests \
  .venv/bin/python -m unittest test_doppler_runtime test_doppler_lookup \
  test_rerank test_rerank_recognition test_calibrated_reranker
```

Physical execution and development selection results belong in the linked
[current status](STATUS.md). No protected recognition/composition evaluation,
UI deployment, or generalization claim follows from this integration.
