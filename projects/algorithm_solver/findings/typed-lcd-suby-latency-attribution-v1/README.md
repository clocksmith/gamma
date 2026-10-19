# Existing-trace composition latency attribution

The retained [nearest-fit baseline](../typed-lcd-suby-nearest-v1/README.md) already
spends more than its unchanged two-second warm decision budget in query embedding
and ranking for 7/10 development-fit and 4/8 development-audit requests. A change
to the graph prediction head alone cannot qualify that path on these inputs.
This is attribution from existing observations, not a new performance campaign.

| Population | Requests | Upstream phase over 2 s | Median query tokens | Median embedding + ranking | Median construction | Median assembly |
|---|---:|---:|---:|---:|---:|---:|
| Development fit | 10 | 7 | 358.5 | 4.014 s | 0.00553 s | 0.00393 s |
| Development audit | 8 | 4 | 237 | 1.982 s | 0.00500 s | 0.00074 s |

All 18 inputs are below the existing 1,024-token cap: none was truncated.
Token counts were computed from the exact retained baseline inputs with the
approved local tokenizer, without an encoder forward pass, training, execution,
download or protected input. Timing values are copied from the original frozen
baseline receipts. Token length is explanatory metadata, not a causal comparison.
Embedding and the small 15-fit-graph ranking operation share one measured phase;
these records cannot attribute individual operators or kernels.

[Summary](summary.json) binds the baseline summary/contract, new development
corpus and tokenizer hashes and retains per-request phase counters. No model,
source representation, token cap, threshold, budget or source graph changed.
The next qualified comparison must charge its complete measured upstream cost.
An encoder/source representation optimization would need a separately frozen
matched development experiment before any latency improvement claim; no such
optimization or new training was run here. No release threshold or protected
composition gate is satisfied by this diagnostic.

Component: algorithm_solver composition. Intent and authority preserved; no
component boundary changed. Evidence: existing frozen baseline phase receipts
plus local tokenizer counts, all 18 untruncated. Raw problem/graph/test contents
remain ignored and local.
