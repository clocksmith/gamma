# Local BITS discovery

256one owns the BITS editor. This adapter serves its existing public files locally
and exposes only `POST /api/bits/recognize`. It returns candidate identities for an
explicit human selection, never solution source or an accepted-answer verdict.
No Firebase configuration or deployed backend is changed.

From the Gamma root, with provisioned Doppler models and the original private
boundary gate available:

```bash
PYTHONPATH=.:projects/algorithm_solver .venv/bin/python -m algsolve.bits_server \
  --public-root ../256one/public \
  --keys projects/algorithm_solver/data/derived/corpus_embedding_keys.json \
  --vectors projects/algorithm_solver/data/derived/corpus_embeddings.npy \
  --gate /absolute/path/to/boundary-gate.json \
  --gate-sha256 ORIGINAL_TRUSTED_GATE_SHA256 \
  --doppler-root ../doppler \
  --embedding-model ../doppler/models/local/qwen-3-embedding-0-6b-q4k-ehf16-af32 \
  --reranker-model ../doppler/models/local/qwen-3-reranker-0-6b-f16-af32
```

Open `http://127.0.0.1:8874/labs/two-button/?recognition=service`. Stop with Ctrl-C. Use a process-group
supervisor with a hard memory and lifetime limit for unattended jobs. The server
binds loopback only; it does not authorize a public reverse proxy. `--surface
browser` selects the existing Doppler browser worker instead of Node. No weights
are downloaded. Models load on the first semantic request; exact title/slug/ID
lookups need no model execution.

The public BITS catalogue must exactly match the vector keys. The index identity
binds vector/key hashes, public packet manifest, original source gate and Doppler
runtime. These are existing frozen Qwen reference document vectors queried with
Doppler embeddings, not a newly trained or qualified index. Semantic retrieval
keeps ten candidates and ranks their permitted public statements (otherwise only
their titles) by yes-minus-no logit. It returns up to three possible matches without
probability claims or automatic acceptance. The default reranker configuration
uses Doppler’s tiled F16 projections and head-128 attention with bounded 512-token
synchronous prefill chunks. It pins the original model manifest and changes no
weights, prompts or candidate count. Pull Doppler’s single-row selected-logit fix
(`d1a8879e`) before using chunked reranking. The generated configuration and its
provenance live under `config/bits-reranker-tiled-v1/`; a mismatching model fails
before loading. `--reranker-config PATH` selects an explicitly supplied alternative
which is also bound into the runtime identity. Truncated queries abstain. A poisoned
runtime is replaced on retry only if its identity is unchanged.

The original source boundary is checked before opening each public statement.
Protected and unknown statement payloads remain closed. The endpoint does not
open solution bodies, private tests, confirmation payloads or qualification
receipts. The response binds the exact request text hash and request ID. No query
text or private artifact path is logged by the HTTP handler. Only one semantic
request executes at a time; concurrent requests fail busy rather than queueing.

Focused checks:

```bash
PYTHONPATH=.:projects/algorithm_solver .venv/bin/python -m pytest -q \
  projects/algorithm_solver/tests/test_bits_recognition.py
```

These tests establish endpoint boundaries and selection mechanics, not population
precision/recall. Recognition qualification, composition effort, human performance
and solution qualification remain separate evidence contracts.

## Static browser publication

The default hosted BITS finder now consumes a public, versioned bundle rather than
requiring the loopback endpoint. Gamma owns its generation and policy; 256one owns
the interface; Doppler owns browser inference and verified model storage. Export
existing document vectors without re-embedding at browser startup:

```bash
PYTHONPATH=.:projects/algorithm_solver .venv/bin/python -m algsolve.export_bits_browser \
  --public-root ../256one/public \
  --keys /absolute/path/to/corpus_embedding_keys.json \
  --vectors /absolute/path/to/corpus_embeddings.npy \
  --gate /absolute/path/to/boundary-gate.json \
  --gate-sha256 ORIGINAL_TRUSTED_GATE_SHA256 \
  --doppler-root ../doppler \
  --model-variants /absolute/path/to/verified-model-variants.json \
  --output ../256one/public/labs/two-button/recognition
```

The model-variant input names embedding/rerank manifest paths, immutable Hugging
Face weight URLs, manifest SHA-256 and variant IDs, and tokenizer SHA-256/size.
Provision it using Doppler's `tools/migrate-rdrr-shard-hashes.js` and independent
pinned-revision LFS verification. Historical nonstandard shard digests are not
accepted by weakening verification. Corrected SHA-256 variants preserve tensor
bytes and recomputed tensor roots; qualification does not transfer automatically.
Only public manifest bytes, pins and immutable weight URLs enter the bundle.
The private input paths and migration receipts are not published.

Export calls the existing boundary gate before opening each statement. It emits
3,353 identities/vectors, 2,872 permitted descriptions with source notices, and
481 title-only records. Restricted competitors remain in retrieval. No solution
bodies, private cases, source gates or qualification receipts are emitted.
Documents, vectors, reranker config and model manifests carry byte counts and
SHA-256 pins; `release.js` pins the bundle manifest. Source vectors, keys, public
packet manifest, exporter bytes and Doppler revision have provenance hashes.

The browser explicitly offers about 1.76 GB of model download, verifies shards and
tokenizers, retains models for repeated queries, and reuses OPFS cache on later
visits. It executes the original instruction, normalization, top-ten retrieval,
bounded reranking overlay and yes-minus-no scoring. Queries stay on the device.
Exact title/slug/ID lookup does not need models. Optional local service behavior
requires `?recognition=service`; browser asset failure never silently selects it.
Storage, unsupported GPU, cancellation and GPU loss have explicit retry paths.

Focused publication and endpoint checks:

```bash
PYTHONPATH=.:projects/algorithm_solver .venv/bin/python -m unittest \
  projects.algorithm_solver.tests.test_bits_browser_export \
  projects.algorithm_solver.tests.test_bits_recognition
```

These establish publication boundaries and mechanics, not precision/recall or a
portable latency claim. Measured browser integration records belong beside the
corresponding deployed 256one revision; older comparison numbers below do not
establish its cold-download or cross-device performance.

## Diagnostics and measured limits

The [retained comparison](../findings/bits-latency-v1/summary.json) profiles one
authored query over ten unchanged candidates. The original resident worker took
77.37 seconds warm, of which 77.01 seconds was reranker execution. The tiled
512-token path took 1.87–1.91 seconds warm in Node and 2.06–2.07 seconds in the
browser. Cold requests took 3.91 and 9.88 seconds respectively. These repeated
query measurements are not population p50/p95, and the 250 ms target remains
unmet. There is no judge in this discovery route. These measurements predate the static browser integration.

All ten candidate rankings and executed tokens matched; maximum paired logit
change was 0.00735. Across the separate 24 consumed development queries with
supplied candidates, all rankings/tokens also matched, with maximum change below
0.00902. Floating-point differences can change threshold decisions: old acceptance
calibration is not promoted to the new runtime. No fresh confirmation is claimed.

For stage timings, replace `algsolve.bits_server` in the startup command with
`algsolve.bits_profile` and add `--query-file PATH --output NEW_DIRECTORY --repeats 3`.
The output binds model/index identities and retains every iteration, including
failures. `algsolve.compare_bits_profiles REFERENCE CANDIDATE --output NEW_JSON`
checks complete profiles for identical input tokens, documents and rankings.
The API response includes timings; detailed diagnostic logits remain outside the
normal browser response. Run under a hard memory/lifetime process-group supervisor.

`algsolve.bits_retrieval_probe` takes the same startup arguments plus `--cohort`,
`--review`, and `--output`; only a hash-bound, independently reviewed development
cohort is accepted. The measured dense retriever hit 15/16 positive targets at
rank one and 16/16 by rank eight over the existing 3,353 vectors. This is not a
3,599-ID test: 727 non-protected eligible identities lack mapped vectors. Existing
protected vectors remain in the frozen index as competing identities; their
statement payloads remain closed. Qualified-source availability never filters
this discovery ranking. Reviewed confusable candidates can still be absent at
rank 32, so target recall alone is not adequate ambiguity evidence.

To regenerate the execution overlay, run `prepare_bits_kernel_config.mjs` with
Doppler root, the provisioned F16 reranker directory, and a new output directory.
It delegates graph compilation and kernel digest checks to Doppler, preserves
weights/manifests, and records provenance. Revalidate changed execution before
replacing the maintained default; generation itself is not qualification.
