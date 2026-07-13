# Offline Teacher And Decoder-Rebuilt Retrieval Investigation

This report answers one question: can embedding teachers, deterministic
Wikipedia rules, dictionaries, routing, and decoder-rebuilt retrieval memory
actually close the `109,500,000` target?

Claim boundary:

```text
This is a strategy and evidence report, not a Hutter proof.
The target is proven only by a full enwik9 archive plus counted decoder bytes,
roundtrip, determinism, and accepted official accounting.
```

## Target Debt

The local target math from `docs/10_95_feasibility_audit.md` is:

```text
best local 100M-calibrated forecast = 110,181,114
target                              = 109,500,000
debt                                =     681,114 bytes
```

The strongest relevant shadow evidence is SRSTC:

```text
SRSTC held-out saved bytes = 916,540
SRSTC net saved bytes      = 900,464
conditional score          = 110,181,114 - 900,464
                           = 109,280,650
margin below target        =     219,350 bytes
```

This is why the lane is credible. The target debt is smaller than the best
measured SRSTC net shadow saving. What is missing is transfer from raw shadow
receipt to counted, deterministic replay on the strongest admissible substrate.
The unchanged aggregate expert has already failed that transfer against an fx2
trace, so the next SRSTC use must target fx2 residuals directly or change the
reversible layout.

The active constructive lane is separate:

```text
candidate     = cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1
10M archive   = 1,638,340 (source-handoff receipt)
roundtrip     = true
determinism   = true
current scope = fresh unchanged guarded 100M replay
```

That gate establishes the exact memory-shaped cmix21 substrate and promotion
path. It does not make the raw SRSTC saving additive. The retired FX2-SC
sidecar remains negative evidence from its canonical `10M` target-ceiling
abort.

Gamma's SAME-R contract now supplies the correct outer experiment for any
teacher-guided successor: freeze the exact FX2 trace, coder, candidates,
student/router budget, split, and payload accounting; compare anchor,
teacher-curated, and deterministic random-control lanes; select only by heldout
codelength after counted bytes. The current Qwen fixed32 selection universe is
retired from promotion for insufficient demonstrated realizable margin, not
disproven. A successor teacher must create new causal experts or state
representations and pass a fresh oracle-economics screen before training. See
`docs/same_r_hutter_strategy_audit.md`.

## What A Tuned Embedding Model Can Do

An embedding model can help as an offline teacher. It can discover structure
that a hand-designed parser or byte model misses:

- page families and namespace regimes;
- title, category, redirect, and disambiguation families;
- template and infobox families;
- citation, URL, and reference-name regimes;
- prose versus table/list/code/math modes;
- chunks whose future continuations are semantically similar even when byte
  suffixes differ;
- deterministic sort or routing keys that improve locality.

The final decoder cannot depend on that model unless the model bytes are
counted and beaten. A Gemma/Doppler/embedding run is useful only when it
distills into small deterministic logic:

```text
offline teacher artifact -> distilled parser/sketch/rule -> counted replay
```

Invalid shortcut:

```text
archive depends on hidden embedding vectors, cluster IDs, or model weights
```

Valid artifact shapes:

- a tiny counted parser rule;
- a counted integer projection seed;
- a deterministic SimHash/minhash feature;
- a page-local trie cap and eviction rule;
- a fixed-point router coordinate;
- a counted table whose byte cost is lower than its measured saving.

The Savant distillation lesson is the governing boundary: powerful teacher
outputs, reference-free routers, embeddings, posterior traces, and oracle
labels are useful only as discovery instruments. The Hutter analogue must be a
single constructive decoder component whose code cost, memory, roundtrip
behavior, determinism, and archive reduction are measured together.

## Decoder-Rebuilt Retrieval Memory

The strongest admissible design is SRSTC: streaming self-referential semantic
retrieval. It builds memory from the already-decoded prefix, so the encoder and
decoder reconstruct the same state without transmitting an index.

Core state:

```text
state_t = f(decoded_bytes_before_t, counted_constants)
p_retrieval_t = g(state_t, base_probability_t)
p_final_t = mix(base_probability_t, p_retrieval_t, online_weights_t)
```

The useful memory is not a shipped embedding table. It is the corpus prefix:
completed spans become future prediction tables after both sides decode them.
Integer sketches approximate semantic similarity while staying deterministic.

The strongest current SRSTC block-posterior receipt reports:

```text
encoded rows             = 524,288,000
held-out saved bytes     = 916,540
code bytes estimate      = 16,076
net saved bytes          = 900,464
max online state bytes   = 22,400,032
block regressions        = 0
```

Known caveat: this is still shadow evidence against the raw order-2 base. It
is target-closing only as a conditional transfer argument. The complete fx2
transfer receipt for the unchanged aggregate expert is negative, so a
constructive path must model fx2 residuals directly, improve reversible layout,
or distill a smaller paying component.

## Existing Repo Evidence Map

The investigation is backed by these local artifacts:

| Artifact | What it proves | What it does not prove |
|---|---|---|
| `docs/streaming_retrieval_receipt_audit.md` | The best SRSTC block-posterior shadow receipt has `900,464` net saved bytes after a `16,076` byte code estimate, which is enough to close the local forecast debt at the raw-shadow boundary. | It is not a compressor result and the unchanged aggregate expert does not transfer positively to fx2. |
| `docs/residual_shadow_matrix.md` | Multiple raw SRSTC receipts are positive; the highest zero-regression ready shadow receipt has `260,560` net saved bytes. | The ready shadow receipt does not close the full forecast debt by itself. |
| `docs/embedding_teacher_rules.md` | Embeddings are admissible as offline teachers only when distilled into counted deterministic rules. | Hidden vectors, cluster labels, model weights, and external indexes are not admissible free state. |
| `tools/embedding_teacher_order.py` and `tools/hierarchical_chunk_embedding_teacher.py` | The repo has machinery for offline semantic discovery and ordering probes. | Current cached hierarchical retrieval probes are weak as direct score evidence. |
| `programs/srstc_raw_order2_aggregate_sketch_v1/` | A decoder-replayable SRSTC codec shape exists and has small-prefix deterministic roundtrip checks. | The standalone package is currently score-negative and is not a target contender. |

The current embedding-teacher rows should be interpreted carefully. The
research register records a raw `64K` hierarchical-retrieval probe with only
`0.083984375` held-out bytes for the best schema/retrieval key against a
`4,096` byte assumed implementation cost, and a bounded `1M` trace-slice probe
with `0` held-out bytes. That does not kill embeddings as teachers. It says
the direct discovered key was too weak, so the useful role is to identify
human-readable deterministic rules, better abstention regions, or compact
integer sketch features for SRSTC and residual/SSE.

The highest-leverage missing artifact is therefore not an embedding model. It
is a target-substrate residual audit that turns the target-closing SRSTC
receipt into one of:

- a no-regression SRSTC receipt with net saved bytes still above `681,114`;
- a causal router that abstains on losing blocks while preserving enough gains;
- a smaller SRSTC component that composes with the strongest admissible
  substrate and survives exact replay after counted code/table bytes.

## Crush Map

This is the component-level hypothesis map. Every row has to survive counted
MDL accounting before it can support a score claim.

| Item | How it can win bytes | Valid final form | Required receipt |
|---|---|---|---|
| Offline embeddings or Gemma/Doppler teachers | Find semantic families, confusing contexts, and repeated continuation patterns that byte suffixes miss. | Human-readable rules, integer sketch features, parser states, or counted tables. | Teacher discovery manifest plus a replayed shadow receipt proving net saved bytes after added bytes. |
| Wikipedia page-family rules | Split articles, redirects, templates, tables, references, lists, and category zones into lower-entropy regimes. | Causal parser state rebuilt from already-decoded bytes. | Per-regime residual table showing gains, losses, and abstention coverage. |
| Decoder-rebuilt dictionaries | Reuse titles, ref names, URLs, infobox keys, template keys, and page-local terms without shipping a static dictionary. | Bounded causal trie or phrase table with deterministic insertion and eviction. | Exact replay hash for table updates plus net byte saving after code cost. |
| Retrieval layout | Turn semantic recurrence into soft copy probabilities for future bytes. | Prefix-built span table using suffixes, span types, SimHash/minhash sketches, and fixed caps. | SRSTC shadow receipt with base bits, retrieval bits, state bytes, and block regressions. |
| Routing | Suppress retrieval where it loses while keeping copy/reference/URL/table gains. | Fixed-point regret router from causal loss and parser/sketch state. | Block-regression audit showing preserved net gain above `681,114` or a composable smaller gain. |
| Tiny SSE/regret correction | Convert systematic residual bias into small probability corrections. | Counted correction table or generated rule set. | Held-out residual receipt with byte cost, train/holdout split, and deterministic replay hash. |

The direct route to crushing the target is not one giant embedding payload. It
is:

```text
teacher finds structure
-> deterministic feature/router/dictionary is distilled
-> shadow coder proves net bytes after counted costs
-> exact replay proves archive, roundtrip, determinism, RSS, and accounting
```

## Measurement Contract

For any embedding-teacher or decoder-rebuilt retrieval experiment to matter, it
must emit a receipt with these fields:

```text
dataset_scope_bytes
base_model_id
candidate_model_id
teacher_inputs
distilled_rule_or_table_bytes
hidden_teacher_state_used_at_decode = false
saved_bits_by_block
regressed_blocks
max_block_regression_bytes
heldout_saved_bytes
net_saved_bytes_after_counted_cost
online_state_bytes
state_update_hash
roundtrip_ok
determinism_ok
```

The promotion threshold for a standalone target-closing residual component is
mechanical:

```text
net_saved_bytes_after_counted_cost >= 681,114
```

or, for a component intended to compose with another lane:

```text
net_saved_bytes_after_counted_cost > 0
and no uncovered block regression
and exact replay survives on the target substrate
```

This contract keeps offline model power useful without smuggling uncounted
knowledge into the decoder. The teacher can choose hypotheses; the final codec
must rebuild every operational bit from the prefix and counted constants.

## How Each Item Can Pay

### Deterministic Rules

Embedding teachers can point to rules such as:

```text
title_family = hash(namespace, lowercase_title_prefix, suffix_class)
template_family = hash(template_name_prefix, normalized_shape)
mode = wiki_state(byte_context, tag_stack_cap, line_shape)
```

These rules pay if they create stable residual buckets for SSE/APM, routing, or
typed copy channels. They fail if the buckets are sparse or require hidden
teacher labels.

### Dictionaries And Tries

A static dictionary is expensive because every byte counts. A decoder-rebuilt
dictionary can be cheaper:

```text
after decoding a title, ref name, URL prefix, template key, or infobox key,
insert it into a bounded causal trie
```

This pays on repeated page-local schema tokens and reference structures. It
must be bounded, evictable, and abstaining so memory and regressions stay under
control.

### Routing

The router should not transmit expert choices. It should replay from causal
loss:

```text
expert = fixed_point_regret_router(history_loss, wiki_state, sketch_state)
```

This can crush the target only if it suppresses losing retrieval buckets while
keeping the high-gain copy/reference/URL/table buckets. The router is the main
tool for converting positive-but-regressing shadow evidence into stable replay
evidence.

### Retrieval Layout

The layout should favor compact, deterministic tables:

- suffix bytes plus span type;
- integer SimHash/minhash sketches;
- bounded nearest-neighbor support;
- type-specific copy channels;
- block fallback and abstention;
- online MDL-value eviction.

This is the direct bridge between semantic recurrence and arithmetic-coder
probabilities. The current SRSTC evidence says this bridge is worth enough
bytes in shadow form to close the local debt.

### Wikipedia Structure

Wikipedia structure matters because enwik9 repeats schema more than generic
English:

- headings;
- links;
- templates;
- infobox keys;
- reference names;
- URLs;
- categories;
- tables;
- list punctuation;
- page-title echoes.

The right use is not a broad transform that risks reversibility. The right use
is causal state that improves probabilities while preserving raw bytes.

## Promotion Path

The investigation supports this path:

1. Let the active unchanged `100M` cmix21 gate finish and record its terminal
   archive, roundtrip, determinism, RSS, identity, and accounting receipts.
2. Run the pinned identical-stream cmix21 component trace and exact FX2
   comparison after the proof boundary. Apply the full-component and fixed-blend
   convex-hull economics gates before causal searches.
3. Use embedding teachers offline only to create new deterministic sketch
   features, page-family keys, abstention rules, or experts after the current
   candidate universe is measured.
4. Re-score SRSTC and residual shadows against the strongest substrate with
   block fallback, type-specific copy channels, and fixed-point regret routing.
5. Require receipts with saved bytes, counted code/table bytes, block
   regressions, state bytes, schema hashes, and deterministic replay hashes.
6. Compile only the smallest paying component into the strongest admissible
   substrate.
7. Run exact prefix replay with roundtrip and determinism.
8. Promote to full `1G` only after exact larger-scope gates and official
   accounting accept the same constructive package.

## Conclusion

The answer is yes: these items can plausibly crush the target, but only in the
distilled decoder-rebuilt form. The repo already has enough shadow evidence to
make SRSTC the most serious target-closing research lane. The missing work is
not another conceptual argument. It is converting offline teacher discoveries
and SRSTC/residual shadow savings into a counted, deterministic replay that
survives target-substrate transfer, block regressions, and official accounting.
