# FX2-SC: Structural-Cognitive Context Mixing

This document is a design thesis and execution roadmap for an `enwik9`
compressor lane that leaves the raw byte stream untouched while feeding
recomputed structural context into a context-mixing backend.

It is not a benchmark result. Measured program scores belong in
`ALGORITHMS.md`, `index.json`, and `results/<program_id>/*.json`. This document
separates the research hypothesis from the empirical ledger so implementation
work can be reviewed without overstating unmeasured claims.

## Top Status

FX2-SC is a novel sidecar/calibration lane, but the primary novel strategy is
now SRSTC / streaming self-referential semantic retrieval. FX2-SC remains
valuable as the outer SSE/APM and structural-state layer that SRSTC can use
after exact shadow evidence exists. The current proof path is still governed by
exact gate artifacts. Use this table before making any claim about progress to
`10.95%`.

| Item | Current value | Evidence boundary |
|---|---|---|
| Best exact `10M` local score | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1`: score `1,882,615`, archive `1,643,289`, program `239,326` | Exact artifact-backed prefix result only. |
| Best exact `10M` cmix21 archive | `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`: archive `1,638,083`, local score `2,202,359` | Exact artifact-backed prefix result; not active because larger-scope RSS behavior is unsuitable. |
| `ppmd21888k` bracket result | Exact `10M` replay passed at archive `1,638,182`; unchanged `100M` promotion failed RSS guard by `36` KiB | Guard receipt: `ppmd21888k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21760k` bracket result | Exact `10M` replay passed at archive `1,638,204`; unchanged `100M` promotion failed RSS guard by `72` KiB | Guard receipt: `ppmd21760k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21632k` bracket result | Exact `10M` replay passed at archive `1,638,229`; unchanged `100M` promotion failed RSS guard by `68` KiB | Guard receipt: `ppmd21632k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21504k` bracket result | Exact `10M` replay passed at archive `1,638,165`; unchanged `100M` promotion failed RSS guard by `72` KiB | Guard receipt: `ppmd21504k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| Active candidate | `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`: exact `1,024` byte replay passed with roundtrip and determinism | Result: `results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-02T143419.json`; guard receipt: `ppmd21376k_1024_determinism_rss_guard.json`. |
| Active gate | `ppmd21376k` unchanged `250,000` byte RSS-guarded determinism replay | Launch or wait for this promotion gate; use terminal driver and RSS receipts before any retune. |
| Best `100M` evidence | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`: metadata-inherited score `15,040,789`, archive `14,857,781`, program `183,008` | Inherited by payload and ordered-stream identity from the verified geometry parent. No exact `100M` result JSON is present in `results/`. |
| Best full `1G` proof | None | The certificate generator reports no verified full-corpus result JSON in this checkout. |
| Best forecast | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`: projected `110,181,114` | Forecast quality: `fx2-calibrated-from-exact-100m`; not a constructive proof. |
| Active blocker | Active `ppmd21376k` `250,000` byte deterministic replay has not produced terminal driver and RSS receipts yet | Do not retune or launch another compression gate while the lock is held. |

## Abstract

The strongest measured context-mixing systems on `enwik9` are already excellent
at byte-level sequence prediction, but they still have to infer Wikipedia's
document structure indirectly from local history. Physical preprocessors try to
help by rewriting, sorting, splitting, or tokenizing the text before a backend
compressor sees it. Those transforms can improve LZMA-like systems, but they
can also damage the historical contiguity that context mixers rely on.

FX2-SC, short for Structural-Cognitive Context Mixing, proposes a different
rule: keep the primary byte stream continuous and unchanged. A deterministic
sidecar parser walks the same bytes in parallel and emits structural context
coordinates such as template hash, argument slot, XML field, table column,
namespace, title-token prefix, citation-name rank, and a small recurrent
trajectory bucket. The backend then uses these coordinates as additional
probability contexts. The archive does not store the sidecar state because the
decoder recomputes it from already-decoded bytes.

The central hypothesis is:

```text
Wikipedia structure should be used as a recomputable predictive lens,
not as an inline text transform.
```

Strategic update: that lens should feed a stronger primary model, SRSTC, when
possible. SRSTC adds self-referential span tables, deterministic sketch
similarity, and patch-copy priors; FX2-SC supplies the causal parser state and
calibration surface.

## Score Contract

The Hutter score is:

```text
S = compressed_archive_bytes + counted_decoder_bytes
```

Lower `S` wins. The archive-only diagnostic is:

```text
b/B = compressed_archive_bytes * 8 / input_bytes
```

`b/B` helps explain entropy, but `S` is the score. Every proposed sidecar
feature must therefore pass both tests:

```text
archive_delta = baseline_archive_bytes - experiment_archive_bytes
program_delta = experiment_decoder_bytes - baseline_decoder_bytes
score_delta = archive_delta - program_delta
```

A feature only matters if `score_delta > 0` at the same input scope with
`roundtrip_ok = true`.

## Why Not More Inline Preprocessing?

This repository already contains useful structural preprocessors. For LZMA2,
stream separation and syntax opcodes can be productive because the backend
benefits from cleaner local symbol distributions. For a mature context mixer,
the tradeoff is more delicate.

Physical transforms create two failure modes:

1. Context shattering. If an inserted opcode or rewritten field changes the
   local bytes around repeated prose, downstream match tables may stop seeing
   the same phrase as the same phrase.
2. Mutual-information starvation. If prose, XML, titles, numbers, and templates
   are split into isolated streams, each stream loses evidence from the
   neighboring streams. A `<title>` boundary, a template pipe, or an XML field
   marker often predicts the next bytes; splitting removes that cue.

FX2-SC avoids both by preserving the raw bytes:

```text
raw decoded bytes -> context mixer -> arithmetic coder
       |
       v
deterministic sidecar parser -> structural context IDs
```

The parser is allowed to know where it is. It is not allowed to rewrite what
the backend sees unless a separate, measured custom-backend experiment proves
that explicit events beat raw coding after all metadata costs.

## Relationship To Existing Code

The idea is not starting from zero. The current repository already has several
pieces that map onto this thesis.

Existing measured or source-backed lanes:

- `schema_title_streams_lzma2_1g_v1` proves typed structural separation can
  improve a strong LZMA2 backend at full-corpus scope.
- `ast_opcode_lzma_v1` proves small syntax opcodes can be effective with a
  low counted program size.
- `typed_anchor_chain_ppmc_v1` proves a custom backend can combine literals,
  raw LZ77 matches, and structural anchor-chain matches over the full corpus.
- `yellow_tucan_structural_range_v5` proves parser state can improve an
  adaptive range coder at small scope.
- `external/cmix21-sidecar` already contains sidecar-style variables such as
  template state, field state, slot state, link/title/category state, numeric
  class, URL state, page kind, column bucket, word hash, and entity recency.

The missing step is disciplined attribution: introduce one context family at a
time, route it through native cmix-sidecar machinery, measure the archive delta,
subtract counted program growth, and retire contexts that do not pay.

## Boundary To Other FSM Clusters

Only the causal-compression cluster applies directly to `enwik9`.

| Cluster or column | Applies to final `enwik9` archive? | Correct role here |
|---|---|---|
| Cluster 1: causal compression | Yes | Main lossless byte-ledger lane: cmix/fx2/cmix21, exact replay, causal side state, counted decoder bytes. |
| Cluster 2: functional tensor representation | No, not directly | Offline teacher only. It may discover clusters, routes, or deterministic rules, but the final archive should not ship a large model unless its byte savings exceed its full counted cost. |
| Cluster 3: deterministic execution runtime | No, except as tooling | Useful for model/runtime reproducibility, not a Hutter decompressor dependency. |
| Descriptor-MoE and FSM-Swarm | No | Relevant to distributed model execution, not to a single-file `enwik9` proof path. |

Therefore FX2-SC should stay small: causal parser state, tiny tables, exact
shadow coding, and final archive replay. Simulatte-style physics ledgers and
Doppler tensor manifests may inspire proof discipline, but they are not
submission artifacts for this corpus.

Cluster 2/3 artifacts only help this project as offline teachers. A Qwen,
Gemma, embedding, descriptor, Doppler, MoE, or swarm system may discover page
families, parser states, or ordering rules. The final `enwik9` decompressor
must ship only the distilled deterministic rule or table, and those bytes must
be counted. A large model artifact is not admissible by implication; it must
beat its full byte, runtime, memory, and reproducibility cost.

## Current Novel Lane Register

| Lane | Mechanism | Why it is novel | Current rule |
|---|---|---|---|
| SRSTC / streaming retrieval mixer | Builds bounded self-referential SimHash/minhash retrieval tables from completed decoded spans and predicts soft patch-copy continuations from similar prior spans. | Converts cosine-style semantic recurrence into the primary deterministic history-derived compressor state. | Must first win exact held-out shadow bytes; then enter as the smallest paying outer SSE/APM, router input, or custom-backend component. |
| Causal residual/SSE patch compiler | Logs base probabilities, groups residuals by deterministic Wiki/XML state, emits tiny outer-SSE corrections. | Turns structural features into byte-counted patches instead of broad transforms. | Shadow-coder savings must exceed code/table bytes; useful as SRSTC calibration. |
| Causal schema trie / seed dictionary | Builds bounded tries from already-decoded titles, refs, URLs, template keys, and page-local terms. | Gets dictionary-like priors without shipping a dictionary payload. | State must be causal, bounded, abstaining, and usable as an SRSTC table family. |
| Embedding-teacher ordering | Uses embeddings offline to find page families, then distills them into deterministic ordering keys or parser states. | Uses neural semantics as discovery, not as shipped decoder state. | Do not ship the embedding model unless its byte cost is beaten. |
| Deterministic expert router / MWCC | Runs tiny prose, markup, URL, numeric, and citation experts and gates them by causal past loss. | Avoids transmitted route tokens by selecting from history. | Expert count and tables must stay small enough to pay under MDL. |
| I-SSA / bounded attractor state | Updates a small integer state vector from decoded bytes and maps it to calibration buckets. | Handles malformed markup as trajectory drift instead of parser failure. | Use only as a soft coordinate; never replace the base compressor. |
| Value-ranked memory lensing | Measures archive damage per KiB saved for PPMD, FXCM, RCM, buffers, and maps. | Treats memory admissibility as an empirical compression allocation problem. | Backup proof lane and baseline while cmix21 candidates are under promotion. |

## Residual Validation Gate

FX2-SC features are not accepted because they are semantically plausible. They
are accepted only when paired prediction evidence pays for the shipped bytes:

```text
net_saved_bytes =
    held_out_shadow_saved_bits / 8
  - added_code_bytes
  - added_table_bytes
```

Promotion requires:

```text
net_saved_bytes > 0
```

and the win must survive block-level inspection. Report total gain, median block
gain, number of winning and losing blocks, largest loss block, and content class
for major losses. A feature that wins only one prefix or one structural region is
a search clue, not a compiled candidate.

Do not use output clamping as a shortcut. Structural state must enter as an
outer SSE/APM coordinate, bounded logit correction, or tiny causal expert that
can abstain when support is weak.

## Mathematical Model

Context mixers combine many model predictions. For a bit `b`, a model emits
`p_i = P(b = 1 | context_i)`. The mixer converts probabilities to logit space,
combines them, and maps the result back to a probability:

```text
stretch(p) = log(p / (1 - p))
X = sum_i w_i * stretch(p_i)
P_mix(b = 1) = sigmoid(X)
```

FX2-SC adds recomputed sidecar coordinates to the set of contexts:

```text
context_i = f(raw_history, sidecar_state)
```

For example, a byte inside a template argument can be keyed by:

```text
template_ctx =
    hash(active_template_name)
  ^ (argument_index_bucket << 8)
  ^ slot_kind_bucket
```

The same byte history can then learn different predictions in different
structural regions:

- prose outside templates,
- template name,
- template argument key,
- template argument value,
- URL slot,
- numeric slot,
- table cell in a specific column.

## Soft Probability Biasing

Hard masks are unsafe. A numeric field can contain citations, words, malformed
markup, ranges, comments, links, or editor-specific spelling. If a coder assigns
zero probability to a byte that appears, decompression fails.

The safe version is soft mixing. Let `P_raw(x)` be the backend's ordinary byte
probability and `P_schema(x | s)` be a schema-biased distribution for the active
sidecar state `s`. Define:

```text
P_safe(x | s) = lambda * P_raw(x) + (1 - lambda) * P_schema(x | s)
```

where `0 < lambda <= 1`. If `P_raw(x)` is nonzero for every byte, then
`P_safe(x | s)` is also nonzero for every byte. Schema-conforming bytes can
become cheaper, while anomalies remain legal. The cost is controlled by the
fallback mass `lambda`; choosing it is an empirical ablation parameter, not a
paper claim.

Example:

```text
field: population
schema-favored bytes: digits, comma, space, hyphen, references markers
fallback: all 256 byte values through P_raw
```

The sidecar may bias; it must not make the arithmetic coder brittle.

## Extended Mathematical Formalism

This section gives the proposed mathematical shape of FX2-SC in implementation
terms. It is a design contract for ablations, not a claim that all components
are implemented.

### Non-Destructive Coordinate Projection

Let the input be an unbroken byte sequence:

```text
B = b_1, b_2, ..., b_N
b_t in A = {0, 1, ..., 255}
```

At byte position `t`, the compressor history is:

```text
H_t = b_1, b_2, ..., b_(t-1)
```

FX2-SC preserves this history exactly. The sidecar parser is a deterministic
automaton `P` over already-seen bytes:

```text
D_t = P(H_t)
D_t = (D_spatial, D_syntax, D_schema, D_semantic)
```

The parser output is a coordinate. It is not an archive payload.

For the first schema ablation, the coordinate is packed into a narrow sparse
key:

```text
K_t =
    (D_schema << 16)
  ^ ((D_semantic & 15) << 8)
  ^ (D_syntax & 15)
```

The practical binding uses existing sidecar fields:

```text
K_template =
    (side_template_hash << 16)
  ^ ((side_template_arg & 15) << 8)
  ^ (side_slot & 15)
```

The masking with `& 15` deliberately keeps the argument and slot coordinates in
a dense local space. The template hash is still sparse, but the low-order
coordinate does not explode into unrelated map regions.

### Coordinate-Gated Logistic Mixing

Context mixers operate at the bit level. Let `y_t` be the active target bit.
Each model `i` emits a probability:

```text
p_(t,i) = P_i(y_t = 1 | H_t)
```

The probability is converted into logit space:

```text
x_(t,i) = stretch(p_(t,i))
stretch(p) = log(p / (1 - p))
```

The sidecar context can be treated as an additional model. For a simple
count-based indirect map:

```text
P_sidecar(y_t = 1 | K_t) =
    (C(K_t, 1) + 1/2) / (C(K_t, 0) + C(K_t, 1) + 1)
```

The mixed logit is:

```text
L_t =
    sum_i w_(t,i) * x_(t,i)
  + w_(t,sidecar) * stretch(P_sidecar(y_t = 1 | K_t))
```

The final bit probability is:

```text
P_mix(y_t = 1) = sigmoid(L_t)
sigmoid(z) = 1 / (1 + exp(-z))
```

Weights adapt online after the true bit is known:

```text
w_(t+1) = w_t + eta * (y_t - P_mix(y_t = 1)) * x_t
```

#### Fixed-Point Weight Saturation And Clipping

Fixed-point implementations need a deterministic saturation rule after each
weight update. Let `M_clip` be the maximum magnitude allowed for a mixer weight.
The projection operator is:

```text
clip(w_i) = max(-M_clip, min(M_clip, w_i))
```

The bounded update is:

```text
w_(t+1) = clip(w_t + eta * (y_t - P_mix(y_t = 1)) * x_t)
```

This applies to ordinary model weights and sidecar-gated weights. The purpose is
not only numeric stability; it is reproducibility. High-frequency structural
contexts such as template slots should not be able to drive a fixed-point mixer
into overflow or saturate adjacent low-frequency contexts.

The sidecar coordinate is therefore not a separate codec. It is an extra
question asked of the existing mixer: "given this structural state, did prior
bits with this key behave differently?"

### Gated Secondary Symbol Estimation

Logistic context mixing can overestimate or underestimate transition
probabilities near structural boundaries. FX2-SC can route the mixed
probability through a Secondary Symbol Estimation, or SSE, stage keyed by the
same sidecar context:

```text
P_sse(y_t = 1) = SSE(P_mix(y_t = 1), K_t)
```

The SSE table tracks the true bit outcome relative to the predicted probability
and learns a local remapping. This lets the model correct structural bias after
the main mixer has produced a probability. For example, a numeric field may
over-predict spaces, or a template boundary may over-predict prose-like
characters. A sidecar-gated SSE can correct those local calibration errors
without requiring the primary logistic mixer to relearn all weights.

This is a proposed integration point, not a separate coder. In a cmix-family
backend, the goal is to let sidecar coordinates participate in the same
nonlinear calibration layer where the strongest final probability corrections
already happen.

### Lossless Rate Ledger

For a future custom-backend lane, FX2-SC can evaluate competing reversible
representations of a span `T`. The selected path is the one with the smallest
coded rate:

```text
mode_selected = argmin(J_literal, J_macro, J_copy)
```

Candidate costs:

```text
J_literal =
    sum_{b in T} -log2 P_mix(b | native_model)

J_macro =
    R_pointer + R_args
  + sum_{b in T} -log2 P_mask(b | D_t)

J_copy =
    R_offset + R_length
```

This is called a rate ledger here rather than a lossy rate-distortion optimizer
because the decoded output must be byte-identical. There is no distortion term;
there are only alternative lossless encodings and their metadata costs.

For `cmix21-sidecar`, this ledger is mostly a research diagnostic. The near-term
implementation should first test sidecar contexts, not explicit macro events.

### Two Safe Masking Forms

The repo should allow two equivalent safety patterns, both nonzero for every
byte.

Backend-fallback mixture:

```text
P_safe(b | s) = lambda * P_raw(b) + (1 - lambda) * P_schema(b | s)
```

Uniform-floor mixture:

```text
P_safe(b | s) = (1 - epsilon) * P_schema(b | s) + epsilon * (1 / 256)
```

#### Bit-Cost Ceiling

For any byte `b`, the uniform-floor form gives:

```text
P_safe(b | s) >= epsilon / 256
```

Taking the negative binary logarithm gives the maximum anomalous-byte cost:

```text
-log2 P_safe(b | s) <= -log2(epsilon / 256)
                         = 8 - log2(epsilon)
```

For example, if `epsilon = 0.01`, a byte that is completely unsupported by the
schema model still has a finite ceiling:

```text
8 - log2(0.01) = 14.643856 bits
```

The first form preserves the backend's native anomaly handling. The second form
is useful in simulators or custom byte coders. If `P_schema(b | s) = 0` for an
unexpected byte, the uniform-floor form still guarantees:

```text
-log2 P_safe(b | s) <= -log2(epsilon / 256)
```

That is the key safety property: malformed syntax is expensive, not impossible.

### Fixed-Point Trajectory Selector

The proposed recurrent component is a selector, not a character predictor. Let
the hidden state be a small integer vector:

```text
h_t in Z^K
```

A deterministic fixed-seed recurrence can update from sidecar coordinates:

```text
h_t = (A * h_(t-1) + B * D_t) mod 2^16
```

where `A` and `B` are integer matrices generated from a fixed seed. No
floating-point state is allowed.

No signed integer operation may be allowed to overflow. In standard C++, signed
integer overflow is undefined behavior and can produce compiler-dependent
optimization paths. A Hutter-valid decoder needs identical reconstruction under
different compilers and architectures, so the recurrent state should use
explicit fixed-width unsigned types and defined modular wrapping:

```cpp
uint32_t acc = uint32_t(a) * uint32_t(prev)
             + uint32_t(b) * uint32_t(coord);
uint16_t next = uint16_t(acc & 0xFFFFu);
```

The rule is simple: use `uint16_t` or `uint32_t` for wrapping state, mask
explicitly, and cast deliberately. Do not rely on `int`, `long`, or accidental
overflow behavior.

If the recurrent update is too noisy or costly, it can be gated by a deterministic
cadence:

```text
if should_update(t):
    h_t = (A * h_(t-1) + B * D_t) mod 2^16
else:
    h_t = h_(t-1)
```

The hidden state is compressed down to a small trajectory bucket:

```text
gamma_t = bucket(norm(h_t)) & 7
```

The bucket may gate context families:

```text
gamma_t = 1  -> favor table/list contexts
gamma_t = 2  -> favor citation and URL contexts
gamma_t = 3  -> favor template boilerplate contexts
```

It must not directly dominate the arithmetic coder. Its purpose is to select
which sparse classical models are likely relevant.

## Prior Art And Novelty

FX2-SC is not a new foundational entropy-coding primitive. It does not replace
arithmetic coding, context mixing, PPM, match modeling, or online adaptation.
Its novelty is architectural: it combines established compression ideas into a
non-destructive topology tailored to the constraints of `enwik9` and the Hutter
score ledger.

### What Is Established Prior Art

Several FX2-SC components have clear historical precedents.

Syntax-directed compression is established. XML-aware systems such as XMill and
XMLPPM showed that structured documents become easier to compress when the
compressor understands tags, fields, and syntactic state. The important lesson
is that document structure carries predictive information. FX2-SC accepts that
lesson but rejects mandatory physical stream splitting for context-mixing
backends.

Context mixing is established. PAQ-family compressors, cmix, and fx2-style
systems combine many specialized predictors using online-learned weights,
secondary symbol estimation, match models, dictionaries, and arithmetic coding.
FX2-SC does not claim to invent this substrate. It treats the substrate as the
model that should receive better structural questions.

Online learning in lockstep is established. Neural and adaptive compressors can
update encoder and decoder state from already-decoded history without storing
the learned state in the archive. FX2-SC borrows that principle, but narrows the
online neural role to small deterministic sidecar gates rather than large dense
character-logit generators.

Smoothing is established. PPM escape mechanisms, Lidstone-style smoothing, and
other nonzero-probability estimators exist to prevent unseen symbols from
becoming impossible. FX2-SC's soft schema biasing is a domain-specific use of
that general principle: every byte remains legal, but the fallback mass changes
according to recomputed Wikipedia structure.

Probabilistic sketches are established. Count-Min Sketch-like structures are
well-known for streaming frequency estimation. In this lane, they are candidate
sidecar memories for long-range frequency and entity hints, not a new
probability-coding primitive.

Rate selection is established. Video codecs use rate-distortion optimization to
choose between competing representations. In a lossless text compressor, the
same discipline can be recast as a rate ledger: literal path, copy path,
sidecar-hinted path, or macro path should win only if the exact coded rate pays
for its metadata.

### What Is Specific To FX2-SC

The main FX2-SC contribution is the continuous-stream sidecar lens. Earlier
schema compressors often physically decompose XML into separate streams or
rewrite source tokens. FX2-SC keeps the source byte order intact and feeds
structure only as recomputed context. This is designed specifically to preserve
the long-range histories, word contexts, and match windows that strong context
mixers already exploit.

The second contribution is the role assigned to structural state. Template
identity, argument index, table column, namespace, title-token prefix, citation
rank, URL state, and numeric class are not serialized as replacement tokens.
They become sparse coordinates for existing predictor maps. That lets the
backend learn different byte probabilities for the same local suffix under
different document states.

The third contribution is bounded cognitive gating. A fixed-point recurrent
state or SSM is not treated as a primary language model. It emits a tiny
trajectory bucket that selects or biases sparse context families. This uses
online sequence state to route classical models instead of forcing a dense
neural model into the byte-coding loop.

The fourth contribution is domain-specific tabular and anchor gating. Raw
MediaWiki tables, citation names, and page titles have localized recurrence
patterns that are invisible to generic byte models until enough examples are
seen. FX2-SC treats those patterns as page-local, bounded sidecar memories.

The fifth contribution is the falsification protocol. FX2-SC is not considered
validated because it is plausible. Each sidecar coordinate must survive an
isolated ablation with a positive `score_delta`, exact roundtrip, and counted
program-size accounting. If a context fails that ledger, it is retired or
redesigned.

Academic positioning:

```text
FX2-SC is a novel compression-system topology and Hutter-specific engineering
synthesis. It is not a new entropy coder or new mathematical primitive.
```

## Five Core Theories

### Theory 1: Deterministic Generative Priors

The large version of this theory is a quantized language model that predicts
tokens and encodes the rank of the true token. Under the Hutter ledger, a large
static model is costly, and dense autoregressive inference is a poor fit for a
single-core byte compressor.

The FX2-SC version is smaller: a deterministic, fixed-point token-class prior.
It does not try to emit full vocabulary logits. It emits cheap sidecar hints:

- likely prose vs. markup,
- likely digit run vs. word run,
- likely URL/path vs. normal English,
- likely list/table rhythm vs. paragraph rhythm.

Closest repository precedent: `purple_parrot_nncp_v1` demonstrates online
neural prediction from scratch, but it is not yet the fixed-point sidecar gate
described here.

### Theory 2: Global Graph Induction And Entity Factoring

Wikipedia is an entity graph: titles, redirects, links, categories, templates,
and repeated citations. A destructive graph compiler would replace text with
entity IDs and store a formatting residual. That risks a large lossless
formatting tax because human-written source varies in spacing, punctuation,
link display text, citation placement, and capitalization.

The FX2-SC version uses graph facts as probability context only:

- current namespace,
- active page title token hashes,
- recent link target hashes,
- category or template family,
- entity recency or move-to-front rank,
- title-to-body prefix match.

Closest repository precedent: article geometry tools, title/link sidecar state,
and `typed_anchor_chain_ppmc_v1` structural keys.

### Theory 3: Morphological And Grammar-Guided Coding

A full grammar parser is fragile on raw Wikipedia. Prose is interrupted by XML,
MediaWiki links, templates, file syntax, tables, references, and HTML entities.
The viable version is shallow and subordinate to schema state.

Track only cheap, deterministic prose features:

- word shape: lowercase, Capitalized, uppercase, mixed, numeric, alphanumeric,
- suffix class: `s`, `ed`, `ing`, `ion`, `ly`, or none,
- punctuation state: after period, after comma, inside quote, normal,
- stable prose span flag,
- title-token or entity-token match flag.

Grammar features should activate only when the sidecar is confident it is in
plain prose. Template, URL, table, and citation states take priority.

Closest repository precedent: wordcode-like transforms and parser-state
experiments. A full grammar sidecar is not implemented.

### Theory 4: Universal Template Schema Contexts

This is the most implementation-ready theory. XML tags, infoboxes, citations,
URLs, dates, coordinates, category links, and table rows are structured
schemas. The sidecar should track where the byte sits inside those schemas and
give the mixer a structural coordinate.

Useful state variables:

- `side_template_hash_`,
- `side_template_arg_`,
- `side_field_`,
- `side_slot_`,
- `side_numeric_class_`,
- `side_url_state_`,
- `side_category_state_`,
- `side_col_bucket_`,
- `side_page_kind_`.

Example:

```text
{{cite web |url=https://example.org |title=Page |date=2026-06-06}}

url slot:   favor URL/domain/path bytes
title slot: favor prose-like bytes
date slot:  favor digit/date punctuation bytes
```

The raw bytes remain unchanged. The schema only changes which probability
tables are asked.

### Theory 5: Bounded Online State-Space Gating

An online State-Space Model, or SSM, is useful only if it stays small,
deterministic, and subordinate. The proposed role is not to replace cmix with a
neural byte model. The role is to produce a tiny trajectory bucket that gates
existing sparse contexts.

Example buckets:

```text
0 neutral prose
1 list or table rhythm
2 citation-heavy prose
3 template boilerplate
4 entity-dense article
5 numeric/date sequence
6 category or link listing
7 unknown/mixed
```

The recurrent update must use fixed-point arithmetic and deterministic integer
state. The output should select or bias context families, not inject dense
neural logits into the primary coder.

## Five Local Entropy Traps

The broad theories above miss several localized Wikipedia patterns that are
worth isolated sidecar ablations.

### 1. Table Coordinates

Wikipedia tables have grid structure. Columns often keep consistent types:
year, country, population, party, score, date, distance, or URL.

Payload:

```text
side_table_depth = table nesting depth bucket
side_table_col = current column bucket
side_cell_class = numeric, prose, URL, date, mixed
```

Example:

```text
| 1995 || United Kingdom || 58,000,000
```

The byte predictor should learn that column 0 looks year-like, column 1
looks entity-like, and column 2 looks numeric-like.

Table parsing needs a truncation guard. MediaWiki tables are often malformed or
nested with local formatting. A missing delimiter should not offset the column
index for the rest of the page. On a hard row marker, force the column state
back to its base coordinate:

```text
if previous_byte == '|' and current_byte == '-':
    side_table_col = 0
```

The same reset policy should be applied at table close, page boundary, and
asset/file boundaries that make table-column state unreliable. The goal is to
contain parser drift to one row or one local structure rather than poisoning all
downstream table coordinates.

### 2. Title-To-Body Priming

The page title often recurs in the body, links, categories, and references.
At a page boundary, hash a small set of title tokens. During body text, expose
whether the current word prefix matches a title token.

Payload:

```text
side_title_prefix_flag
side_title_prefix_rank
side_title_prefix_len_bucket
```

This is stronger than a generic word model because it resets per page.

### 3. Namespace Partitioning

Mainspace articles, category pages, template pages, file pages, talk pages, and
user pages have different byte distributions. Namespace state is cheap and
persistent across a page.

Payload:

```text
side_namespace_id
side_page_kind
side_category_state
```

This prevents category-list syntax and template meta-language from diluting
normal article prose contexts.

### 4. Numeric Successor Tracking

Chronological lists and tables often contain runs like `1991`, `1992`, `1993`
or numbered entries. Byte predictors do not directly understand arithmetic
successors.

Payload:

```text
side_numeric_successor_flag
side_numeric_delta_bucket
side_digit_position_bucket
```

This must be a soft context only. It should never force a digit.

### 5. Citation Anchor Chains

Reference names are arbitrary strings that repeat inside a page:

```text
<ref name="smith2004">...</ref>
<ref name="smith2004" />
```

Payload:

```text
side_ref_name_mtf_rank
side_ref_prefix_len_bucket
side_ref_context_active
```

A tiny page-local move-to-front queue is enough to tell the mixer that a
seemingly odd string is likely a prior citation anchor.

### 6. XML Metadata And ISO Timestamp Model

Wikipedia revision headers contain constrained metadata strings, including ISO
timestamp blocks and numeric contributor identifiers.

Payload:

```text
side_xml_timestamp_flag
side_timestamp_char_index
side_xml_numeric_field_flag
```

Example:

```text
2026-06-06T15:00:00Z
```

The sidecar should track the character index inside an active `<timestamp>`
block. In ISO-like timestamp text, fixed positions strongly predict separators:
index 4 is `-`, index 7 is `-`, index 10 is `T`, and later fixed positions are
colon or `Z` candidates depending on the exact format seen in the corpus. This
is a narrow metadata model, not a general date parser. It should activate only
inside verified XML timestamp fields.

## Execution Roadmap

The roadmap uses the measured-result vocabulary from `README.md`. Each phase
needs a control run, an experiment run, a roundtrip check, and a score ledger.

### Phase 1: Schema Baseline

Hypothesis:

```text
Template hash, argument index, field, and slot coordinates improve prediction
without requiring new parser logic.
```

Payload:

```text
sidecar_template_ctx =
    (side_template_hash << 16)
  ^ ((side_template_arg & 15) << 8)
  ^ (side_slot & 15)
```

Integration target:

- `external/cmix21-sidecar/src/context-manager.*`,
- `external/cmix21-sidecar/src/predictor.cpp`,
- one gated `Indirect` context family using existing map machinery.

Pass:

```text
score_delta > 0
roundtrip_ok = true
same input hash as control
```

Kill:

```text
score_delta <= 0
or roundtrip failure
or program bytes exceed archive savings
```

### Phase 2: Soft Symbol Reduction

Hypothesis:

```text
Value class, URL state, numeric class, and table coordinates reduce local byte
entropy when applied as soft sidecar contexts.
```

Payload examples:

```text
side_numeric_class
side_url_state
side_table_col
side_table_depth
side_cell_class
```

Safety rule:

```text
No hard masks. Every byte remains legal through P_raw fallback.
```

Pass:

```text
schema_plus_symbol_score < schema_only_score
roundtrip_ok = true
no arithmetic-coder zero-probability path
```

Kill:

```text
hard-mask crash
or sidecar parser desync
or noisy contexts dilute previous schema gains
```

### Phase 3: Lexical Priming And Semantic Recency

Hypothesis:

```text
Page-local title tokens, citation anchors, and recent link targets predict
strings that ordinary byte contexts relearn repeatedly.
```

Payload examples:

```text
side_title_prefix_rank
side_ref_name_mtf_rank
side_link_recency
side_entity_recency
side_word_hash
```

Memory rule:

```text
Use bounded page-local queues. Avoid unbounded dictionaries.
```

Pass:

```text
phase3_score < phase2_score
roundtrip_ok = true
bounded memory layout
```

Kill:

```text
large or scattered tables
or rare-event savings fail to pay for code
```

### Phase 4: Active Geometry

Hypothesis:

```text
Article family, template recurrence, namespace, and page-kind contexts let the
mixer adapt to page regimes without physically splitting streams.
```

Safer first version:

```text
Compute page-family contexts in stream order.
Do not reorder pages.
```

Aggressive version:

```text
Reorder only if the exact permutation recovery cost is included in S.
```

Payload examples:

```text
side_namespace_id
side_page_family
side_page_kind
side_template_recurrence_rank
side_cluster_local_schema_rank
```

Pass:

```text
geometry_context_score < phase3_score
roundtrip_ok = true
permutation cost accounted for if sorting is used
```

Kill:

```text
unaccounted permutation metadata
or context-shattering from physical reorder
or gains do not reproduce at broader scopes
```

### Phase 5: Bounded SSM Gating

Hypothesis:

```text
A tiny fixed-point recurrent state can classify document trajectory and select
which sparse sidecar contexts should dominate.
```

Payload:

```text
side_trajectory_bucket = 0..7
```

Rules:

- Use integer arithmetic only.
- Emit a small gate or bucket, not dense byte logits.
- Keep the ordinary statistical models in charge.
- Verify archive determinism across compilers and hosts before promoting.

Pass:

```text
phase5_score < phase4_score
roundtrip_ok = true
compressed archive hash reproducible under the determinism contract
```

Kill:

```text
cross-host nondeterminism
or recurrent state dilutes stable sidecar contexts
or added code size exceeds measured archive savings
```

## Proposed Patch Worksheet

This section is intentionally a worksheet, not a claim that the patch is
already applied.

Narrow phase-1 concept:

```cpp
// context-manager.h
unsigned long long sidecar_template_ctx_ = 0;
```

```cpp
// context-manager.cpp, after native side_template_* state updates
sidecar_template_ctx_ =
    ((unsigned long long)side_template_hash_ << 16)
    ^ ((unsigned long long)(side_template_arg_ & 15) << 8)
    ^ (side_slot_ & 15);
```

```cpp
// predictor.cpp, inside AddSidecar()
#ifdef SIDECAR_TEMPLATE_ONLY
  AddModel(new Indirect(manager_.nonstationary_,
                        manager_.sidecar_template_ctx_,
                        manager_.bit_context_,
                        220,
                        manager_.shared_map_));
#endif
```

The implementation must be adjusted to the actual class names and object
lifetimes in `external/cmix21-sidecar`. The key constraint is isolation: the
phase-1 experiment should add only one new context family so the result can be
attributed.

## Result Note Template

Use this for each ablation note:

```markdown
## <experiment_id>

Hypothesis:
<one sentence>

Payload:
- <state variable>
- <state variable>

Control:
- program:
- input size:
- data hash:
- archive bytes:
- program bytes:
- S:

Experiment:
- program:
- input size:
- data hash:
- archive bytes:
- program bytes:
- S:

Ledger:
- archive_delta:
- program_delta:
- score_delta:
- roundtrip_ok:
- compressed_sha256:

Verdict:
PREPROCESSOR_WINS | PREPROCESSOR_LOSES | INCOMPLETE | NON_DETERMINISTIC
```

## Open Risks

1. Context dilution: adding many sparse contexts can make the mixer adapt to
   noise rather than structure.
2. Program-size creep: small C++ additions still count if they expand the
   decoder binary or bundled source.
3. Memory locality: role-specific queues and entity memories must be bounded.
4. Parser drift: encoder and decoder must update sidecar state identically.
5. Slice overfitting: prefix wins do not prove full-corpus wins.
6. Hard-mask brittleness: every byte must remain legal.
7. Reordering cost: physical page sorting is not free unless exact recovery is
   deterministic or its metadata is counted. If the corpus contains `M`
   independent page frames, arbitrary reordering selects one of `M!`
   permutations. A lossless decoder needs the reverse permutation, whose
   information floor is:

   ```text
   L_perm = ceil(log2(M!))
          ~= ceil(M * log2(M / e) + 0.5 * log2(2 * pi * M))
   ```

   This lower bound must be charged to the archive or the counted decoder
   assets during geometry-sort validation. A sort that improves backend
   compression but omits the recovery ledger is an invalid proxy win.
8. Boundary-lag gradient desynchronization: when the stream exits a dense
   structural regime and enters another regime, online weights can lag the new
   context. Updates near the boundary may still reflect the old distribution,
   creating bit leaks at template-to-prose, table-to-prose, or XML-to-text
   transitions. Boundary contexts should therefore be isolated or explicitly
   bucketed during ablations.

## Canonical Execution Order

1. Keep cmix21 memory-shaped candidates moving through exact gates.
2. Reproduce the public `fx2-cmix` lane for official-accounting calibration.
3. Build exact base-probability logs only where they do not disturb output.
4. Run residual heatmaps and shadow coding by causal Wiki/XML state.
5. Schema baseline: template hash, argument index, field, slot.
6. Soft symbol reduction: value class, URL/numeric/date, table coordinates.
7. Lexical priming: title tokens, citation MTF, link/entity recency.
8. Namespace and page-kind partitioning.
9. Active geometry as stream-order context.
10. Reversible geometry sorting only with permutation accounting.
11. Role-specific copy hints.
12. Shallow grammar in stable prose spans.
13. Bounded fixed-point SSM gating.
14. Custom backend event tests for ideas that do not fit cmix-sidecar.

## References

- `README.md` for scoring math, result JSON interpretation, and verdict
  vocabulary.
- `ALGORITHMS.md` for measured custom algorithm mechanisms and benchmark
  status.
- `docs/official_accounting_checklist.md` for promoted-candidate official
  score accounting.
- `docs/shadow_coder_spec.md` for probability-log and residual/SSE validation
  requirements.
- `docs/embedding_teacher_rules.md` for offline embedding-teacher boundaries.
- `external/cmix21-sidecar/` for the current sidecar-oriented C++ substrate.
- `typed_anchor_chain_ppmc_v1` for the strongest measured custom entropy
  backend artifact currently present in this checkout.
- `schema_title_streams_lzma2_1g_v1` and `ast_opcode_lzma_v1` for measured
  structural preprocessing wins with LZMA2 backends.

Prior-art families to cite if this is expanded into an external paper:

- XMLPPM and XMill for syntax-directed XML compression.
- PAQ, cmix, and fx2-style systems for context mixing and online model
  weighting.
- PPM escape estimation and Lidstone-style smoothing for nonzero-probability
  modeling.
- NNCP-style neural text compression for synchronized online learning.
- Count-Min Sketch for compact streaming frequency estimation.
- HEVC-style rate selection as the conceptual ancestor of the proposed lossless
  rate ledger.
