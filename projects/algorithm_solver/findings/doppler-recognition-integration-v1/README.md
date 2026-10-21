# Doppler recognition integration

Component: Gamma algorithm recognition, goals 1a/1b. Intent preserved. Doppler
owns GPU execution; Gamma owns retrieval, source approval and public judging.
No Doppler runtime/kernel changes, model downloads, protected scoring or UI
deployment. [Run guide](../../doppler-recognition.md).

The new retained worker executes real Qwen embedding and reranker models through
Doppler's Node WebGPU API. Input hashes, response IDs, token identity, vector
shape/finiteness, model identity and timeouts are checked. Twenty-four focused
tests passed, including the Node input contract and timeout cleanup.

The active index contains 3,288 eligible entries, excluding 65 protected aliases.
Document vectors remain the existing hash-pinned Transformers Qwen reference
matrix. Query vectors are Doppler Q4_K embeddings. This mixed pairing is explicit,
separately calibrated, and does not replace the original CPU qualification.

## Consumed development descriptions

All 24 existing descriptions completed: 16 known problems, four ambiguous requests
and four easy out-of-domain controls. Historical clarification labels map to
abstention. Thresholds were fitted separately on these same development rows.
Both routes ran on Apple M3 using Node WebGPU / Metal.

| Recognition stage | Correct first choice / 16 known | Accepted correct | Wrong accepted | Abstained / 24 | Median recognition time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Doppler embedding + lookup | 11 | 3 | 0 | 21 | 198 ms |
| Same lookup + Doppler reranking | 6 | 4 | 0 | 20 | 21.27 s |

These are pre-public-check selection results, not returned-code accuracy or a
held-out estimate. The hosts were not exclusive. Reranking adds one accepted
development match at substantially greater cost and worsens first-choice identity;
it remains optional, with no default promotion. The existing editor still uses
its prior path.

## Physical checks

On Apple M3, the corrected adapter returns 1,024-dimensional embeddings, separates
an unrelated description, ranks the relevant candidate ahead of an irrelevant
one, and reproduces the exact embedding after switching to reranking and back.

On 128's Radeon 8060S, three requests covered exact lookup, informal embedding
lookup, and informal lookup with reranking. Each selected
`lc:two-sum-ii-input-array-is-sorted`, returned approved stored code, and passed
two public examples in Gamma's Linux sandbox. The informal requests supplied
an explicit interface and examples. The exact request bypassed inference;
the others exercised Doppler embeddings and optional reranking. These three
requests establish the integration paths, not general recognition accuracy.

## Preserved failures and reproduction

The first worker passed token arrays as prompt text. Its vectors were finite but
semantically wrong; the 24-case development check accepted nothing. The failed
index and receipts remain under `runs/doppler-recognition-m3-v1` and
`runs/doppler-recognition-embedding-dev-v1`. The fix passes text with explicit
`inputIds` and verifies the returned tokens. A Node boundary test prevents that
specific regression.

The corrected full-recomputation attempt remains partial under
`runs/doppler-recognition-m3-v2`. The active
`runs/doppler-recognition-reference-v3` uses the original pinned document vectors.
Both completed calibrations and detailed physical receipts remain under the
paths hashed in [summary.json](summary.json). Code-bearing answer receipts and
corpus artifacts remain private.

Next: improve requirement-aware selection using development evidence, preserving
this Doppler execution path and measuring complete answers. Fresh independent
evaluation and any editor/default change require their own acceptance evidence.
