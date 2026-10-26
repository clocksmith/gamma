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

Open `http://127.0.0.1:8874/labs/two-button/`. Stop with Ctrl-C. Use a process-group
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
probability claims or automatic acceptance. Reranker prefill uses explicit
128-token synchronous chunks, recorded in the runtime identity, to bound each
GPU submission without truncating descriptions. Truncated queries abstain. A poisoned
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
