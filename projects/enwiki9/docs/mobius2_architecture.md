# MOBIUS-2: two-lane self-referential language codec

Status: recorded research architecture; unmeasured; zero score credit.

This document records the proposed MOBIUS-2 architecture and its falsifiable
research boundaries. It does not authorize a queue entry, native integration,
or a larger gate. Before either lane runs, its implementation proposal, frozen
format, exact inputs, source allowance, and kill condition must be materialized
through `tools/enwiki9_lab.py`.

The objective remains a constructive official full-corpus score:

```text
score <= 108,000,000 bytes
scope_bytes == 1,000,000,000
roundtrip_ok == true
```

The current full-1G score is unknown. The best counted forecast remains
109,389,323 bytes, 1,389,323 bytes above the target. MOBIUS-2 receives no
forecast or frontier credit until a counted native replay exists.

## Thesis

MOBIUS-2 does not ship a frontier language model. Frontier models may be used
offline to propose boundaries, equivalence classes, questions, grammars, or
quantization layouts. The counted decoder contains only deterministic source,
tables, grammar data, and model data that are sufficient to reproduce the raw
corpus exactly.

The codec has two independently gated lanes:

1. LOGOS: a paid, self-describing, many-use grammar that regenerates exact WRT
   spans and omits their truth bits from the literal arithmetic payload.
2. NOEMA: a compact deterministic dyadic hierarchy that predicts the literal
   remainder and, eventually, the LOGOS control stream.

The joint accounting identity is:

```text
M2 total = control archive
         + literal archive
         + LOGOS package
         + NOEMA package
         + retained Gamma package
```

Separate projected gains are never added. The lanes combine only through one
exact joint replay.

## Lane 1: LOGOS

### Compression-native concepts

LOGOS does not grant score credit to ordinary words, tokens, parts of speech,
or semantic labels. Spans share a concept only if one deterministic expansion
program plus paid slots and surface corrections is shorter than their exact
literal coding.

A discovery system may factor a candidate description as:

```text
z = (d, f, r, e, q, m, s, epsilon)

d        discourse function
f        semantic frame
r        role topology
e        entity signature
q        quantitative or temporal shape
m        morphology and lexical realization
s        exact Wikipedia, XML, and surface shell
epsilon  Gamma residual-loss class
```

Human-readable examples include definitional leads, office timelines,
administrative chains, measurement assertions, and citation shells. These
names have no intrinsic value: each class survives only if exact minimum
description length accounting pays for its rule, descriptors, slots,
commands, exceptions, framing, and decoder source.

### Self-interrogating summaries

Each span receives a variable-depth binary description. A deterministic
question DAG chooses the next binary question from the already decoded
summary state; only the answer is coded. A frontier model may propose the
question inventory offline, but decompression uses compact question and
transition identifiers, not question text or model inference.

The same language operates at several scales:

```text
bytes
  -> morphemes
  -> lexical realizations
  -> clauses
  -> sentences
  -> paragraph plans
  -> page archetypes
  -> corpus ontology
```

The primitive meta-language is initially limited to:

```text
ASK
FRAME
SLOT
EXPAND
COPY
PATCH
LITERAL
```

Ontology definitions are themselves encoded with this language. Self-reference
is stratified: rule `v` may reference rule `u` only when `rank(u) < rank(v)`.
Bootstrap opcodes are literal, and all subsequent references are backward.
The result is a finite self-hosting DAG, not a logical cycle.

### State-preserving generation

For each selected span LOGOS emits one of:

```text
GEN(rule_id, slots)
COPY(previous_span, length)
PATCH(edit_program)
LITERAL(length)
```

`GEN` and `COPY` reconstruct exact WRT bytes without consuming literal truth
bits. Every reconstructed bit is nevertheless fed through the state-mutating
paths of Gamma and NOEMA. Literal bits are decoded from the combined predictor
and then update both models. After each operation, the model states must equal
the states produced by ordinary decoding of the same original bit prefix.

This is the same state-preservation invariant investigated by Route E, but the
source of reconstruction is materially different. Route E allowed one earlier
page prototype per target page and searched all 14,535 legal pairs in the exact
opening-1M population. No page paid its reference and finite command cost;
actual E2 was 15 bytes larger than the parent. LOGOS is viable only if
transmitted rules are reused across enough pages to amortize their definitions.
Minimum-copy, prototype-count, distance-window, and integer-code changes do not
rescue Route E and must not be relabeled as LOGOS.

### Exact LOGOS objective

For page `x_i`, descriptor `d_i`, ontology `O`, slots, commands, and literal
surface remainder `r_i`:

```text
C_i = L(d_i | O)
    + L(slots_i | d_i)
    + L(commands_i)
    + L_Gamma(r_i | history_i)
    + L(framing_i)

O* = argmin_O [L_self(O) + sum_i min_{d_i in O} C_i]
```

`L_self(O)` includes the complete self-encoded ontology and bootstrap. Literal
fallback is mandatory at every selection point.

## Lane 2: NOEMA

### Dyadic fractal-memory predictor

NOEMA begins as a residual specialist over exact Gamma probabilities. One
small recurrent transition is reused at each hierarchical level. At a frozen
patch boundary, a lower-level state is quantized and passed upward:

```text
z_k^(level) = Q_level(h_k^(level))
h_(k+1)^(level+1) = F(h_k^(level+1), z_k^(level), level_embedding)
```

Candidate levels are:

```text
0  byte and bit-prefix state
1  dynamic byte patch
2  lexical or phrase event
3  clause or sentence
4  paragraph
5  page
6  page family or corpus phase
```

The next-bit residual correction is a sparse deterministic mixture of these
states and the current binary-prefix node. The corrected probability is
emitted in Gamma's existing legal integer P1 domain.

### Surprise-driven persistent memory

A bounded online memory may update only when realized residual surprise crosses
a frozen threshold. Keys derive from already decoded semantic summaries and
byte state. Slot choice, learning rate, decay, clipping, saturation, and ties
are all deterministic. There is no decode-time backpropagation.

This feature receives independent attribution. The hierarchy must be compared
with surprise memory disabled, and persistent memory cannot rescue a hierarchy
that fails its primary gate.

### Dynamic compute

The local path may run continuously. Higher-level cells run only at frozen
entropy or semantic boundaries. Persistent memory updates only on declared
surprise events. A confidence gate may skip an expensive correction path when
its output cannot pay, but the gate itself and every state transition must be
decoder reproducible and counted.

## Deterministic numeric contract

Floating-point training is permitted; uncontrolled floating-point decoding is
not. The exported machine uses dyadic block-floating values:

```text
value = signed_integer_mantissa * 2^shared_exponent
```

Required runtime rules:

- Fixed-width or software-wide intermediates with explicit overflow behavior.
- One specified round-to-nearest-even operation after aligned integer dot
  products.
- Walsh-Hadamard rotation blocks with dimension `4^k`, so normalization is an
  exact power-of-two shift.
- Structured low-bit weights: ternary blocks, lattice or codebook indices, and
  sparse int8/int16 escapes.
- Integer lookup tables or piecewise dyadic polynomials for nonlinearities.
- No platform `exp`, `tanh`, floating softmax, or reduction-order dependence.
- Canonical symbol-ID tie breaking.
- Every table, index stream, model blob, and decoder delta charged once.

For a larger LOGOS alphabet, a 24-bit cumulative-frequency total is a proposed
Q0 dimension, not assumed credit. Frequencies must be positive and normalized
by a deterministic largest-remainder rule.

## Archive and decoder order

The proposed archive layout is:

```text
M2 header
LOGOS bootstrap primitives
self-encoded ontology and question DAG
compressed NOEMA parameter package
page-by-page summary and control stream
literal arithmetic stream
optional sparse surface-exception stream
```

Decoder order:

1. Decode bootstrap, ontology, and NOEMA package.
2. Decode a page summary before it controls that page.
3. For `GEN` or `COPY`, reconstruct exact WRT bytes and update Gamma and NOEMA
   without consuming literal truth bits.
4. For `LITERAL` or `PATCH`, predict, arithmetic-decode the exact remainder,
   and update both models.
5. Apply the official WRT inverse.
6. Verify raw length and hash.

There is no circular undecoded dependency: definitions reference only lower
ranks, each summary token is predicted from prior state, and every generated
byte is known before it updates later state.

## Frozen research gates

### LOGOS Q0

The exact opening-1M WRT stream, endpoint428 parent P1 trace, complete-page map,
raw inverse, and parent archive are the starting population. Before execution,
freeze the primitive opcodes, rule-ranking contract, factor inventory, one
question-DAG construction algorithm, command coder, source allowance, and
literal fallback.

Controls:

```text
S0  exact parent replay
S1  surface and XML-only many-use grammar
S2  full compression-native semantic grammar
SR  semantic labels shuffled within matched page families
SL  identical descriptors with every expansion forced literal
```

Authorization requires all of:

```text
parent payload identity                 exact
control-stream decode                   exact
complete WRT reconstruction             exact
official raw inverse                    exact
second archive                          byte-identical
S2 gross gain                           >= 3,000 B/M
S2 projected net after source           >= 2,100 B/M
S2 total                                < S1 total
S2 total                                < SR total
sealed chronological group              positive
```

No grammar-width, category-count, or question-depth rescue sweep follows a
miss. Before full construction, LOGOS should produce a paid upper-bound
certificate demonstrating that many-use rule definitions could plausibly
clear the gate; otherwise it remains parked.

### NOEMA Q0

NOEMA may begin on the exact existing trace with byte-derived patch boundaries.
Before execution, freeze one shared cell, state width, level count, surprise
memory rule, dyadic quantizer, model-package ceiling, and output factorization.

Controls:

```text
N0  exact Gamma replay
N1  flat single-level model at matched package size
N2  recursive fractal hierarchy
NS  summary states shifted across pages
NM  hierarchy with surprise memory disabled
```

Authorization requires all of:

```text
development gain                        positive
sealed holdout gain                     >= 3,000 gross B/M
projected package-adjusted gain          >= 2,100 B/M
distant reset-window result             positive
N2 total                                < N1 total
N2 total                                < NS total
model blob second hash                  identical
adjusted P1 stream second hash          identical
arithmetic decode                       exact
```

NOEMA must first include a headroom certificate proving that the candidate
information source is absent from the already-tested flat recurrent and
residual neighborhoods. Architectural labels alone do not distinguish it from
CHIRON or other terminal small residual models.

All successor implementations also obey
`docs/mobius2_noema_causal_replay_contract.md`, which freezes byte-causal
frontier, ordered-merge, checkpoint-replay, matched-control, serialized-model,
ROCm-proof, and exact two-layer replay requirements.

## Package budget and joint gate

Initial incremental ceiling:

```text
LOGOS ontology plus decoder delta        192 KiB
NOEMA model plus tables                  128 KiB
framing and source reserve                64 KiB
total                                    384 KiB = 393,216 bytes
```

At the current 1,389,323-byte forecast debt, the joint design needs at least
1,782,539 gross full-corpus bytes merely to cover debt plus this maximum
incremental package. The 2,100 B/M net research gate remains the safer
promotion threshold.

Only after both isolated lanes pass may one canonical 10M joint replay run.
That replay must:

- construct one actual joint archive rather than add projected lane gains;
- save at least 30,000 gross archive bytes;
- project at least 21,000 net bytes at 1G package amortization;
- remain positive on an untouched distant population;
- report literal two-part economics separately;
- prove predictor-state equality after every generated span;
- measure the update-only runtime path; and
- reproduce a byte-identical second archive.

A pass authorizes native integration and a 100M gate, not a 1G claim.

## Planned artifacts

When the lanes are independently claimed, use the canonical adaptive workflow
and these names unless the frozen proposal records a versioned successor:

```text
docs/mobius2_logos_q0_plan.md
docs/mobius2_noema_q0_plan.md
docs/mobius2_joint_accounting_contract.md
programs/mobius2_logos_q0_v1/
programs/mobius2_noema_q0_v1/
programs/mobius2_joint_q1_v1/
results/mobius2_logos_q0_v1/
results/mobius2_noema_q0_v1/
results/mobius2_joint_10m_v1/
```

Do not create ad hoc launch scripts or a second queue. Tools, candidates,
receipts, mutations, and conclusions remain owned by the existing adaptive
workflow and canonical registers.

## Prior evidence boundary

MOBIUS-2 is not evidence that semantic compression or a hierarchical model
pays. It is a structured successor hypothesis. Existing failures impose these
constraints:

- Route E retires single-prior-page state-preserving prototype bypass. LOGOS
  must demonstrate shared many-use grammar amortization.
- Route D retires the selected timestamp-envelope rank/parity mechanism; it
  supplies no general semantic-grammar credit.
- CHIRON and other flat residual failures require NOEMA to prove hierarchy-
  specific headroom and beat a matched-package flat control.
- Route C's missing under-target teacher does not block offline proposal
  generation, but frontier-model codelength receives no score credit.
- WikiIR, page-delta, and stream-transform results require state identity and
  complete control-stream costs rather than transformed-stream estimates.

## Research references

The following references and interpretations were supplied with the proposal.
They are discovery leads, not verified evidence or score-bearing receipts in
this recording pass:

1. Language modeling and compression: <https://arxiv.org/abs/2309.10668>
2. Byte latent transformer and byte-patching direction:
   <https://arxiv.org/abs/2412.09871>
3. Large Concept Models: <https://arxiv.org/abs/2412.08821>
4. Long-context compression and memory: <https://arxiv.org/abs/2305.14788>
5. Low-bit rotation and quantization direction:
   <https://arxiv.org/abs/2402.04396>
6. Nacrith neural-compression preprint:
   <https://arxiv.org/abs/2602.19626>
7. Adaptive binary-question compression direction:
   <https://arxiv.org/abs/2604.02343>
