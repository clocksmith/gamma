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
