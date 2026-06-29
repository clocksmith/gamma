# Structural-Cognitive Context Mixing: A Recomputable Sidecar Lens for Lossless Wikipedia Compression

**Document type:** paper-style design thesis

**Companion implementation roadmap:** [FX2_SC.md](FX2_SC.md)

**Corpus:** `enwik9`, the first \(10^9\) bytes of the English Wikipedia XML dump

## Abstract

Lossless compression of the 1 GB `enwik9` corpus is a benchmark for practical
sequence modeling under a strict accounting rule: the score \(S\) is the sum of
compressed payload bytes and counted decoder bytes. Mature context-mixing
systems already exploit deep byte histories, word contexts, match models,
adaptive probability maps, and online-learned mixing weights. Their remaining
weakness is not lack of generic sequence capacity; it is that Wikipedia's
schema, template, table, citation, and entity structure is only inferred
indirectly from the byte stream.

This paper defines Structural-Cognitive Context Mixing, abbreviated FX2-SC, as
a non-destructive sidecar architecture for exploiting that structure. FX2-SC
preserves the raw byte stream exactly and runs a deterministic parser in
parallel with the encoder and decoder. The parser emits recomputable structural
coordinates at each byte position. These coordinates are not serialized into
the archive. They are used as sparse context keys, calibration gates, and
bounded recurrent selectors for an existing context-mixing backend.

The proposed contribution is architectural rather than primitive. FX2-SC does
not introduce a new entropy coder, nor does it replace arithmetic coding,
context mixing, Prediction by Partial Matching (PPM), or match coding. It
instead formalizes a topology that couples syntax-directed compression,
sidecar state reconstruction, gated secondary symbol estimation, fixed-point
online adaptation, and lossless rate accounting without shattering the
historical byte context used by high-order mixers.

## 1. Problem Statement

Let the input corpus be a byte sequence

\[
B = (b_1, b_2, \ldots, b_N), \qquad b_t \in \mathcal{A}, \quad
\mathcal{A} = \{0,1,\ldots,255\}.
\]

The Hutter-style score is

\[
S = L_{\text{archive}} + |D_{\text{decoder}}|,
\]

where \(L_{\text{archive}}\) is the compressed payload size and
\(|D_{\text{decoder}}|\) is the counted decoder footprint. A structural feature
is useful only if its archive-byte reduction exceeds its counted decoder growth:

\[
\Delta S =
(L_{\text{baseline}} - L_{\text{experiment}})
- (|D_{\text{experiment}}| - |D_{\text{baseline}}|) > 0.
\]

The engineering challenge is that Wikipedia has strong structure, but many
obvious transforms damage the exact evidence that context mixers use. Physical
stream splitting can isolate XML fields, titles, prose, timestamps, and
templates into cleaner local streams. That helps some dictionary and LZMA-style
backends. For context mixers, however, it can remove mutual information between
neighboring byte regimes. A `<timestamp>` tag predicts digits; a template pipe
predicts argument syntax; a title field predicts later body text. Splitting
these signals into separate files can starve the mixer of useful cross-stream
evidence.

FX2-SC therefore imposes the following constraint:

\[
\text{The byte history observed by the backend is never rewritten.}
\]

The compressor may parse structure. It may not mutate the primary stream unless
a separate lossless rate ledger proves that an explicit event representation
pays for all metadata and recovery costs.

## 2. Architectural Thesis

At position \(t\), the ordinary compression history is

\[
\mathcal{H}_t = (b_1, b_2, \ldots, b_{t-1}).
\]

FX2-SC defines a deterministic parser \(\mathcal{P}\) over already-decoded
history:

\[
\mathbf{D}_t = \mathcal{P}(\mathcal{H}_t).
\]

The sidecar state \(\mathbf{D}_t\) may include structural axes such as

\[
\mathbf{D}_t =
\begin{bmatrix}
D_{\text{spatial}} \\
D_{\text{syntax}} \\
D_{\text{schema}} \\
D_{\text{semantic}} \\
D_{\text{trajectory}}
\end{bmatrix}.
\]

These axes describe where the byte occurs in the Wikipedia rendering process:
page kind, namespace, template identity, argument index, table coordinate, XML
field, title-token recurrence, citation-anchor rank, URL state, numeric class,
and a small recurrent trajectory bucket.

The critical property is recomputability:

\[
\mathbf{D}_t^{\text{encoder}} = \mathbf{D}_t^{\text{decoder}}
\]

because both sides derive \(\mathbf{D}_t\) from the same decoded prefix
\(\mathcal{H}_t\). No sidecar stream is transmitted.

## 3. Sparse Context Projection

The first implementation target is a schema coordinate derived from existing
sidecar fields. A compact key is formed by bit-packing structural state:

\[
K_t =
(D_{\text{schema}} \ll 16)
\oplus ((D_{\text{semantic}} \ \&\ 15) \ll 8)
\oplus (D_{\text{syntax}} \ \&\ 15).
\]

For the concrete template ablation:

\[
K_{\text{template}} =
(\texttt{side\_template\_hash} \ll 16)
\oplus ((\texttt{side\_template\_arg} \ \&\ 15) \ll 8)
\oplus (\texttt{side\_slot} \ \&\ 15).
\]

The low-order buckets are deliberately bounded. A sparse context is useful only
if it clusters examples. If argument or slot state explodes into a high-cardinal
coordinate, the map disperses statistics and becomes noise.

## 4. Coordinate-Gated Context Mixing

Context mixers operate at the bit level. Let \(y_t \in \{0,1\}\) be the current
target bit. Model \(i\) emits

\[
p_{t,i} = P_i(y_t = 1 \mid \mathcal{H}_t).
\]

The probability is mapped into logit space:

\[
x_{t,i} = \operatorname{stretch}(p_{t,i})
= \log \frac{p_{t,i}}{1 - p_{t,i}}.
\]

The sidecar key \(K_t\) contributes an additional probability estimate. A
simple count-form model is

\[
P_{\text{sidecar}}(y_t = 1 \mid K_t)
=
\frac{C(K_t,1) + \frac{1}{2}}
     {C(K_t,0) + C(K_t,1) + 1}.
\]

The mixed logit is then

\[
\hat{L}_t =
\sum_{i=1}^{M} w_{t,i} x_{t,i}
+ w_{t,\text{sidecar}}
  \operatorname{stretch}(P_{\text{sidecar}}(y_t = 1 \mid K_t)).
\]

The final bit probability is

\[
P_{\text{mix}}(y_t = 1) =
\sigma(\hat{L}_t)
= \frac{1}{1 + e^{-\hat{L}_t}}.
\]

Online adaptation minimizes local binary cross-entropy. In the floating-point
idealization:

\[
\mathbf{w}_{t+1}
=
\mathbf{w}_{t}
+ \eta (y_t - P_{\text{mix}}(y_t = 1)) \mathbf{x}_t.
\]

For a Hutter-grade implementation, the actual update must be fixed-point and
bounded:

\[
\mathbf{w}_{t+1}
=
\Pi\left(
\mathbf{w}_{t}
+ \eta (y_t - P_{\text{mix}}(y_t = 1)) \mathbf{x}_t
\right),
\]

with element-wise clipping

\[
\Pi(w_i) = \max(-M_{\text{clip}}, \min(M_{\text{clip}}, w_i)).
\]

This prevents high-frequency structural keys from driving mixer weights into
overflow or saturating adjacent low-frequency contexts.

## 5. Gated Secondary Symbol Estimation

Secondary Symbol Estimation (SSE) is a nonlinear calibration stage used by
high-performance compressors to correct biased probability estimates. FX2-SC
extends the sidecar from the primary mixer into the calibration layer:

\[
P_{\text{sse}}(y_t = 1)
=
\operatorname{SSE}(P_{\text{mix}}(y_t = 1), K_t).
\]

The value \(K_t\) gates a local remapping table. The table updates online after
the true bit is known, allowing structural contexts to correct systematic
errors without forcing the main mixer to relearn every boundary behavior.

Examples:

- inside a numeric template field, the primary mixer may over-predict spaces;
- at a template-to-prose boundary, it may over-predict markup;
- inside a URL, it may under-predict punctuation such as `/`, `?`, `&`, and `=`;
- inside an XML timestamp, it may under-predict fixed separator positions.

Sidecar-gated SSE is therefore a natural integration point for FX2-SC because
the sidecar coordinate is not only a predictive feature; it is also a
calibration coordinate.

## 6. Soft Schema Biasing

Hard masks are invalid for noisy Wikipedia source. A field that appears numeric
can contain references, ranges, words, HTML entities, comments, malformed
syntax, or editor-specific annotations. Assigning zero probability to any byte
risks arithmetic-coder failure.

FX2-SC allows soft schema biasing. One safe form mixes the backend's native
probability with a schema prior:

\[
P_{\text{safe}}(b \mid s)
=
\lambda P_{\text{raw}}(b)
+ (1-\lambda) P_{\text{schema}}(b \mid s),
\qquad 0 < \lambda \le 1.
\]

Another safe form allocates an explicit uniform floor:

\[
P_{\text{safe}}(b \mid s)
=
(1-\epsilon) P_{\text{schema}}(b \mid s)
+ \epsilon \frac{1}{256}.
\]

If the schema assigns zero probability to an anomalous byte, then

\[
P_{\text{safe}}(b \mid s) \ge \frac{\epsilon}{256}.
\]

The maximum anomalous-byte code length is therefore

\[
-\log_2 P_{\text{safe}}(b \mid s)
\le
-\log_2 \frac{\epsilon}{256}
=
8 - \log_2 \epsilon.
\]

For \(\epsilon = 0.01\), this ceiling is

\[
8 - \log_2(0.01) = 14.643856 \text{ bits}.
\]

The conclusion is operational: malformed syntax becomes expensive, not
impossible.

## 7. Fixed-Point Trajectory Selector

FX2-SC may use a small recurrent state to summarize broad document trajectory,
but this state must not become a dense neural byte predictor. Its job is to
gate existing sparse context families.

Let the hidden state be

\[
\mathbf{h}_t \in \mathbb{Z}^K.
\]

A deterministic integer recurrence can be written as

\[
\mathbf{h}_t =
(\mathbf{A}\mathbf{h}_{t-1} + \mathbf{B}\mathbf{D}_t)
\bmod 2^{16},
\]

where \(\mathbf{A}\) and \(\mathbf{B}\) are fixed integer matrices generated
from a deterministic seed.

The C++ implementation must avoid signed overflow. State variables should use
fixed-width unsigned types and explicit masks:

```cpp
uint32_t acc = uint32_t(a) * uint32_t(prev)
             + uint32_t(b) * uint32_t(coord);
uint16_t next = uint16_t(acc & 0xFFFFu);
```

The trajectory is reduced to a tiny gate:

\[
\gamma_t = \operatorname{bucket}(\|\mathbf{h}_t\|) \ \&\ 7,
\qquad
\gamma_t \in \{0,\ldots,7\}.
\]

Example gates:

| \(\gamma_t\) | Interpretation | Contexts to favor |
|---:|---|---|
| 0 | neutral prose | word/byte contexts |
| 1 | list or table rhythm | table column contexts |
| 2 | citation-heavy prose | ref-name and URL contexts |
| 3 | template boilerplate | template hash and slot contexts |
| 4 | entity-dense article | title/link/entity contexts |
| 5 | numeric/date sequence | numeric and timestamp contexts |
| 6 | category or link listing | category/link contexts |
| 7 | mixed or unknown | neutral fallback |

## 8. Local Entropy Traps In Wikipedia

FX2-SC targets several localized structures that generic byte models learn only
after repeated exposure.

### 8.1 Table Coordinates

MediaWiki tables often preserve column-local type:

```text
| 1995 || United Kingdom || 58,000,000
```

Column 0 may be year-like, column 1 entity-like, and column 2 numeric-like.
Useful payload:

```text
side_table_depth
side_table_col
side_cell_class
```

The parser must include a truncation guard:

```text
if previous_byte == '|' and current_byte == '-':
    side_table_col = 0
```

The same reset policy applies at table close, page boundary, and file/asset
boundaries. This prevents one malformed row from poisoning downstream
coordinates.

### 8.2 Title-To-Body Priming

At page start, the parser hashes a small set of title tokens. During body text,
it exposes whether the current word prefix matches one of them:

```text
side_title_prefix_flag
side_title_prefix_rank
side_title_prefix_len_bucket
```

This captures the fact that the page title is likely to recur in prose,
links, categories, and references.

### 8.3 Namespace Partitioning

Mainspace articles, category pages, template pages, file pages, user pages, and
talk pages have different byte distributions. Namespace and page-kind state are
cheap persistent priors:

```text
side_namespace_id
side_page_kind
side_category_state
```

### 8.4 Numeric Successor Tracking

Chronological tables and lists often contain arithmetic progressions:

```text
1991, 1992, 1993
```

Payload:

```text
side_numeric_successor_flag
side_numeric_delta_bucket
side_digit_position_bucket
```

This must be a soft context. It may suggest the next digit pattern; it must not
force one.

### 8.5 Citation Anchor Chains

Wikipedia reference names are arbitrary but page-local:

```text
<ref name="smith2004">...</ref>
<ref name="smith2004" />
```

A bounded move-to-front queue can expose recurrence:

```text
side_ref_name_mtf_rank
side_ref_prefix_len_bucket
side_ref_context_active
```

### 8.6 XML Metadata And ISO Timestamps

Revision headers contain constrained metadata such as timestamps and numeric
contributor identifiers:

```text
2026-06-06T15:00:00Z
```

Payload:

```text
side_xml_timestamp_flag
side_timestamp_char_index
side_xml_numeric_field_flag
```

Inside a verified `<timestamp>` block, fixed character positions strongly
predict separators. Index 4 is `-`, index 7 is `-`, index 10 is `T`, and later
positions are colon or terminal-marker candidates depending on the observed
format. This is a metadata model, not a general natural-language date parser.

## 9. Lossless Rate Ledger

For a custom backend, structural transforms should be selected by exact rate
accounting rather than global heuristics. For a span \(\mathcal{T}\), define:

\[
\operatorname{mode}^*
=
\arg\min_{\mathcal{M} \in \{\text{Literal}, \text{Macro}, \text{Copy}\}}
J_{\mathcal{M}}.
\]

Candidate costs:

\[
J_{\text{Literal}}
=
\sum_{b \in \mathcal{T}}
-\log_2 P_{\text{mix}}(b \mid \mathcal{M}_{\text{native}}),
\]

\[
J_{\text{Macro}}
=
R_{\text{pointer}} + R_{\text{args}}
+
\sum_{b \in \mathcal{T}}
-\log_2 P_{\text{mask}}(b \mid \mathbf{D}_t),
\]

\[
J_{\text{Copy}}
=
R_{\text{offset}} + R_{\text{length}}.
\]

This is not lossy rate-distortion optimization. There is no distortion term.
It is a lossless rate ledger over alternative reversible encodings. For the
cmix-sidecar lane, the near-term form is not explicit macro selection; it is
sidecar context injection. Explicit events belong in a custom backend until
they prove their metadata cost.

## 10. Reordering And Permutation Cost

Article sorting can improve locality, but it is not free. If \(M\) independent
page frames are reordered arbitrarily, the decoder must recover one of \(M!\)
possible permutations.

The information floor is

\[
L_{\text{perm}} =
\lceil \log_2(M!) \rceil.
\]

By Stirling approximation,

\[
L_{\text{perm}}
\approx
\left\lceil
M\log_2\left(\frac{M}{e}\right)
+ \frac{1}{2}\log_2(2\pi M)
\right\rceil
\quad \text{bits}.
\]

Any geometry-sort experiment must charge this cost to either the archive or
counted decoder assets unless the inverse order is derived deterministically
from data already available during decompression. A sort that omits this ledger
is an invalid compression claim.

## 11. DOPPLER-REPLOID Software Boundary

FX2-SC can be named as two mutually gated implementation layers:

```text
DOPPLER:
Deterministic Out-of-band Parallel Predictor Linking Entropy to REPLOID

REPLOID:
Reversible Entity-gated Predictive Lens Optimizing Intermediate DOPPLER
```

DOPPLER is the streaming predictor boundary. It lives conceptually at the
`predictor.cpp` layer: it receives recomputed sidecar coordinates, packs them
into sparse keys, and routes them through `Indirect`-style predictor maps or
SSE calibration tables.

REPLOID is the symbolic observer boundary. It lives conceptually at the
`context-manager.cpp` layer: it parses already-decoded bytes, maintains bounded
page-local memories, updates fixed-point trajectory state, and exposes the
current structural matrix to DOPPLER.

The closed loop is:

```text
raw byte history
    -> REPLOID symbolic lens
    -> DOPPLER sparse predictor activation
    -> context mixer / SSE / arithmetic coder
    -> decoded byte history
```

### 11.1 DOPPLER Interface

The DOPPLER boundary can be represented by a compact coordinate structure:

```cpp
struct DopplerCoordinates {
    uint32_t template_hash;
    uint8_t template_arg;
    uint8_t slot_kind;
    uint8_t table_column;
    uint8_t xml_field;
};
```

The corresponding context key is:

```cpp
uint64_t K =
    (uint64_t(coords.template_hash) << 32)
  ^ (uint64_t(coords.template_arg & 15) << 28)
  ^ (uint64_t(coords.slot_kind & 7) << 24)
  ^ (uint64_t(coords.table_column & 15) << 20)
  ^ (uint64_t(coords.xml_field & 15) << 16)
  ^ uint64_t(trajectory & 7);
```

The mask widths are part of the statistical design. They keep low-order
coordinates dense enough to train while leaving the high-order template hash
available for schema identity.

A trajectory gate prevents context dilution:

```cpp
static const uint8_t kGate[8] = {
    0b00000001, // neutral prose
    0b00000110, // markup and template states
    0b00001000, // table states
    0b00000010, // URL and reference states
    0b00000000, // reserved
    0b00000000, // reserved
    0b00000000, // reserved
    0b00000001  // fallback
};

bool active = (kGate[trajectory & 7] & (1u << (slot_kind & 7))) != 0;
```

If `active` is false, the DOPPLER context family is skipped for that byte or
bit. This preserves the capacity of the raw sequence models in regimes where
the structural coordinate is not expected to help.

### 11.2 REPLOID Lens

REPLOID maintains the symbolic state that DOPPLER consumes. A minimal boundary
is:

```cpp
class ReploidLens {
public:
    void ProcessByte(uint8_t byte);
    DopplerCoordinates Coordinates() const;
    uint8_t Trajectory() const;

private:
    uint16_t ssm_state_[8];
    uint8_t trajectory_;
    // Bounded page-local queues for titles, links, refs, and entities.
};
```

The fixed-point update must use explicit unsigned modular arithmetic:

```cpp
uint32_t acc = uint32_t(input) * uint32_t(i + 1)
             + uint32_t(ssm_state_[i]) * 3u;
uint16_t update = uint16_t(acc & 0xFFFFu);
```

No signed overflow is permitted. REPLOID must be deterministic under GCC,
Clang, MSVC, x86_64, and ARM64 if the same decoded byte prefix is supplied.

### 11.3 Gated Probability Mixture

Let \(P_{\text{raw}}(y_t = 1 \mid \mathcal{H}_t)\) be the probability emitted
by the ordinary predictor ensemble. Let \(P_{\text{DOPPLER}}(y_t = 1 \mid K_t)\)
be the probability from the active sparse structural key. Let
\(\gamma_t \in \{0,\ldots,7\}\) be the REPLOID trajectory bucket.

The gate can be written as

\[
P_{\text{mix}}(y_t = 1)
=
(1-\lambda_{\gamma_t})
P_{\text{raw}}(y_t = 1 \mid \mathcal{H}_t)
+
\lambda_{\gamma_t}
P_{\text{DOPPLER}}(y_t = 1 \mid K_t),
\]

where \(\lambda_{\gamma_t} \in [0,1]\). A structured regime such as template,
table, URL, or timestamp state may raise \(\lambda_{\gamma_t}\). Noisy prose may
lower it toward zero.

In a cmix-style backend, this interpolation can be implemented directly,
through mixer weights, through sidecar-gated SSE tables, or by choosing whether
to activate a sidecar `Indirect` family for the current bit. The ablation should
test those choices separately.

### 11.4 Verification Ledger

DOPPLER-REPLOID variants must be tested as isolated compile variants. The
minimum ledger is:

```text
control_archive_bytes
experiment_archive_bytes
control_decoder_bytes
experiment_decoder_bytes
archive_delta = control_archive_bytes - experiment_archive_bytes
program_delta = experiment_decoder_bytes - control_decoder_bytes
score_delta = archive_delta - program_delta
roundtrip_ok
input_hash
archive_hash
```

The pass condition is:

\[
\Delta S > 0
\quad \land \quad
\texttt{roundtrip\_ok} = \texttt{true}.
\]

The verification script should use the same input bytes, compare decoded output
with the original input, and report both archive and counted decoder sizes. The
script is part of the empirical harness, not evidence by itself.

## 12. Prior Art And Novelty

FX2-SC is best described as an architectural synthesis. Its components have
clear precedents:

- XMLPPM and XMill established syntax-directed compression for structured
  documents.
- PPM escape mechanisms and Lidstone-style smoothing established nonzero
  probability floors.
- PAQ, cmix, and fx2-style compressors established high-order context mixing,
  online model weighting, SSE, and arithmetic coding.
- NNCP-style neural compressors established synchronized online learning from
  decoded history.
- Count-Min Sketch established compact streaming frequency estimation.
- Video-codec rate selection established explicit rate-ledger thinking for
  competing representations.

The specific FX2-SC contributions are:

1. A continuous-stream sidecar lens that preserves byte history while exposing
   schema state.
2. Sparse structural coordinates for template, table, title, reference,
   namespace, URL, numeric, and XML metadata regimes.
3. Sidecar-gated SSE calibration rather than only primary-mixer feature
   injection.
4. Bounded fixed-point recurrent trajectory selection instead of dense neural
   byte logits.
5. A falsification protocol requiring each context to pass the \(S\)-ledger
   with exact roundtrip.

Thus FX2-SC is not a new entropy coder. It is a Hutter-specific compression
system topology for using recomputable Wikipedia structure without destroying
the evidence that context mixers already exploit.

### 12.1 Current Repository Mapping

The current repository separates proof-bearing implementation from research
supporting machinery:

| Item | Repository role | Final-archive role |
|---|---|---|
| `cmix21` memory shaping | Active target lane for archive slope and admissibility. | Direct candidate substrate if it survives `1G` and official accounting. |
| FX2-SC residual/SSE compiler | Structural patch lane for tiny causal corrections. | Possible add-on only if exact shadow coding proves positive MDL. |
| Causal schema trie / seed dictionary | Research lane for history-derived structural priors. | Possible add-on only with bounded state and no uncounted dictionary. |
| Embedding-teacher ordering | Offline discovery lane for semantic clusters and deterministic keys. | No shipped model unless counted savings exceed model bytes. |
| Functional tensor descriptors and runtime manifests | Model/runtime research in other repositories. | Not part of the `enwik9` decompressor unless distilled to tiny counted rules. |

This keeps the novelty claim narrow. FX2-SC does not assert that external
embedding models, distributed runtimes, or physics-style ledgers are part of a
valid Hutter submission. They are useful only when they produce a small,
deterministic rule that improves exact compressed bytes after all costs are
counted.

## 13. Empirical Rollout

The paper version intentionally does not claim measured wins for unrun
features. The companion roadmap in [FX2_SC.md](FX2_SC.md) defines pass/kill
gates. The execution order is:

1. Schema baseline: template hash, argument index, field, slot.
2. Soft symbol reduction: URL, numeric, timestamp, date, and table class.
3. Lexical priming: title tokens, citation MTF, link/entity recency.
4. Namespace and page-kind partitioning.
5. Active geometry as stream-order context.
6. Reversible geometry sorting only with permutation accounting.
7. Role-specific copy hints.
8. Shallow grammar in stable prose spans.
9. Bounded fixed-point SSM gating.
10. Custom backend event tests for explicit macro and copy paths.

Each phase must report:

\[
\Delta S =
(L_{\text{baseline}} - L_{\text{experiment}})
- (|D_{\text{experiment}}| - |D_{\text{baseline}}|),
\]

plus input hash, archive hash, counted program bytes, and `roundtrip_ok`.

## References

1. Cheney, J. XMLPPM: XML Compression using PPM.
2. Liefke, H. and Suciu, D. XMill: an Efficient Compressor for XML Data.
3. Mahoney, M. Adaptive Weighing of Context Models for Lossless Data Compression.
4. Knoll, B. cmix lossless data compression program family.
5. Bellard, F. NNCP-style neural lossless text compression.
6. Cormode, G. and Muthukrishnan, S. Count-Min Sketch frequency estimation.
