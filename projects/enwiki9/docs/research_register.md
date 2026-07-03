# enwiki9 Research Register

This register tracks strategy and algorithm research separately from measured
candidate proof. It is a map from idea to local implementation, not a scoreboard.

Claim rule:

```text
Research status is not compression proof.
Promotion requires exact receipts: result JSON, shadow-coder receipt, or guard
receipt depending on the lane.
```

Strategy pivot: SRSTC / streaming self-referential semantic retrieval is the
primary novel algorithm lane. `cmix21`, `fx2`, residual/SSE, schema tries,
embedding teachers, MWCC, and I-SSA remain active backup lanes or components;
they are not discarded, and they are not promoted without receipts.

## Active And Proposed Lanes

| Lane | Foundation | Local files | Current evidence | Promote gate | Kill gate |
|---|---|---|---|---|---|
| SRSTC / streaming self-referential retrieval | Causal k-nearest continuation memory over deterministic SimHash/minhash sketches, self-referential span tables, patch-copy priors, and fixed-point regret routing | `docs/streaming_retrieval_mixer.md`, `tools/streaming_retrieval_mixer_plan.py`, `tools/streaming_retrieval_shadow.py`, `tools/streaming_retrieval_raw_shadow.py`, `results/streaming_retrieval_shadow/` | Complete-block raw receipts are now positive through `8,192K`; the best receipt saves `112,212` held-out bytes and `99,924` net bytes after a `12,288` byte code estimate, with `0` block regressions. A `4,096K` complete-block confirmation is active. | Exact shadow coder shows positive held-out net bytes after counted code/table cost, adjacent-scope confirmation stays positive, then the smallest winning component survives prefix replay. | Requires shipping an embedding/index payload, duplicates existing match-model signal, exceeds memory cap, shows concentrated prefix-only gains, or fails when integrated into the replayed compressor. |
| `cmix21` memory-shaped text mode | PAQ/cmix-style context mixing, PPMD, match modeling, SSE/APM calibration | `CMIX21_LOCK_SAFE_QUEUE.md`, `docs/cmix21_memory_valves.md`, `tools/cmix21_package_candidate.py`, `tools/cmix21_gate_decider.py` | Exact `10M` replays exist for `ppmd22272k`, `ppmd21888k`, `ppmd21760k`, `ppmd21632k`, and `ppmd21504k`; prior unchanged `100M` promotions failed RSS. Active promotion lane is `ppmd21504k`, with exact `10M` replay passed and unchanged `100M` gate running. | Same candidate passes `10M`, `100M`, and then `1G` with roundtrip, determinism, and RSS guard. | Any gate fails roundtrip/determinism, or RSS fails and a lower same-surface cut is cheaper than preserving it. |
| FX2-SC causal residual/SSE | Context mixing plus secondary symbol estimation; Wikipedia parser state as outer calibration only | `FX2_SC.md`, `FX2_SC_PAPER.md`, `docs/shadow_coder_spec.md`, `docs/residual_shadow_matrix.md`, `tools/fx2_residual_shadow_matrix.py` | Cached matrix has positive measured or held-out shadow rows but no constructive residual certificate. | Held-out shadow-saved bytes exceed counted code/table bytes, then exact prefix replay passes. | Gains are concentrated in one block, fail held-out shadow coding, or require primary-context hash fragmentation. |
| Causal schema trie / seed dictionary | Adaptive dictionaries and PPM-style online history, but derived only from decoded history | `docs/algorithm_cards.md`, `docs/shadow_coder_spec.md`, `FX2_SC.md` | Design-only in this checkout. | Shadow coder proves exact-byte savings from trie priors with bounded memory and counted code. | Trie grows beyond the memory budget, predicts weakly outside source blocks, or needs future corpus metadata. |
| Embedding-teacher ordering/routing | Offline semantic clustering and article-family discovery; final payload must be deterministic rules | `docs/embedding_teacher_rules.md`, `tools/embedding_teacher_order.py`, `tools/hierarchical_chunk_embedding_teacher.py`, `tools/hierarchical_retrieval_shadow.py` | Cached hierarchical-retrieval shadow rows now appear in `docs/residual_shadow_matrix.md`. The raw `64K` probe found only `0.083984375` held-out bytes for the best schema/retrieval key against `4,096` assumed code bytes; the bounded `1M` trace-slice probe found `0` held-out bytes. | Teacher discovers a tiny deterministic rule that improves exact shadow or replay score after counted bytes. | Improvement requires shipping model/index bytes, or the distilled key remains orders of magnitude below its counted code/table cost. |
| I-SSA bounded attractor state | Robust integer state-space tracking as parser-state replacement | `I_SSA_LOCK_SAFE_REPORT.md`, `FX2_SC.md`, `tools/fx2_issa_shadow_search.py`, `docs/residual_shadow_matrix.md` | Bounded raw-log probe on `residual_apm_1m_mode_charclass_b050` found `1` held-out byte over `260,000` held-out rows. This is a weak positive shadow signal, not a feature-promotion result. | A bounded integer state improves held-out outer-SSE shadow bytes by enough to clear counted implementation bytes and then survives prefix replay. | State adds CPU/code cost without distributed held-out savings, or behaves like a noisy parser hash. |
| Deterministic MWCC router | Expert routing from causal rolling log-loss, with no transmitted route token | `RESIDUAL_ROUTER_LOCK_SAFE_REPORT.md`, `tools/fx2_mwcc_router_shadow.py`, `docs/shadow_coder_spec.md`, `docs/residual_shadow_matrix.md` | Bounded raw-log probe on `residual_apm_1m_mode_charclass_b050` saved `2` same-coder bytes but `0` held-out bytes across `260,000` held-out rows; current receipt is `flat_shadow`. | Router selection improves held-out shadow-coded bytes after counted table/code size and does not destabilize replay. | Expert overhead exceeds measured savings, held-out savings remain flat, or selected experts collapse to base model. |
| Descriptor/embedding model payloads | Functional tensor descriptors and neural compression research | `docs/embedding_teacher_rules.md`, external model-runtime docs outside this Hutter lane | Out-of-scope for final payload unless distilled into tiny deterministic logic. | Only distilled deterministic compressor logic enters the Hutter candidate with counted bytes. | A neural model, embedding index, or descriptor shard must be shipped and its byte cost exceeds archive savings. |

## Reading Order

1. `docs/status_receipt.md` for the active gate.
2. `docs/streaming_retrieval_mixer.md` for the primary SRSTC strategy.
3. `docs/algorithm_cards.md` for plain mechanisms and current scores.
4. `docs/best_results.md` for compact exact top rows by measured scope.
5. `CMIX21_LOCK_SAFE_QUEUE.md` for the active memory-valve decision tree.
6. `FX2_SC.md` and `FX2_SC_PAPER.md` for residual/SSE and sidecar components.
7. `docs/shadow_coder_spec.md` before trusting any residual or router claim.

## External Anchors

These are the primary or near-primary references used to keep the local
strategy register honest.

| Source | Link | Local use |
|---|---|---|
| Large Text Compression Benchmark rules | https://www.mattmahoney.net/dc/textrules.html | Confirms that the score counts compressed `enwik9` plus the decompressor archive and runtime files. |
| Large Text Compression Benchmark table | https://www.mattmahoney.net/dc/text.html | Keeps result language aligned with benchmark scope and accounting. |
| cmix reference page | https://www.byronknoll.com/cmix.html | Anchors the context-mixing, single-pass bit prediction, SSE/APM, and arithmetic-coding substrate. |
| cmix source repository | https://github.com/byronknoll/cmix | Source reference for the `cmix21` family being memory-shaped here. |
| fx2-cmix repository | https://github.com/kaitz/fx2-cmix | Public Hutter-family reference for NLP, online reverse dictionary transform, Wikipedia transform, and article ordering. |
| Hutter Prize FAQ | https://prize.hutter1.net/hfaq.htm | Scope and competition context; local claims still require full `1G` official-accounting receipts. |

## Promotion Discipline

Do not promote an idea from this register because it is elegant. Promote only
when the receipt type matches the claim:

| Claim | Required receipt |
|---|---|
| Exact prefix candidate | Driver result JSON with roundtrip true. |
| Deterministic prefix candidate | Driver result JSON with determinism true or byte-equal replay. |
| Memory-safe candidate | RSS guard receipt under the selected guard. |
| SRSTC feature | Streaming retrieval shadow receipt with counted implementation bytes, deterministic table update hashes, and held-out net savings. |
| Residual/SSE feature | Shadow-coder receipt with counted implementation bytes. |
| Full target claim | Full `1G` official-accounting receipt with score at or below `109,500,000`. |
