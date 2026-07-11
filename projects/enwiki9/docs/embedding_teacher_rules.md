# Embedding-Teacher Rule Distillation

Embedding models can help `enwik9` only as offline teachers unless their full
artifact bytes are counted and beaten. The final Hutter decompressor should
ship tiny deterministic rules, not a large embedding model. The active
target-bearing candidate is
`fx2_sidecar_geometry_title_dictcmix_zlibpy_min_v1`; teacher work should feed
residual/layout discovery around the strongest substrate, not raw uncounted
model knowledge.

## Correct Use

Use Qwen/Gemma-style embeddings or other semantic models to discover:

- page families;
- namespace and title patterns;
- template families;
- citation and reference clusters;
- URL and infobox regimes;
- ordering keys that improve locality;
- structural modes where the base compressor has residual error.

Then distill the discovery into one of:

- a deterministic parser state;
- a small hash projection;
- a bounded causal trie rule;
- a hand-written title or namespace key;
- a deterministic SimHash/minhash sketch used by
  `docs/streaming_retrieval_mixer.md`;
- a tiny table whose bytes are counted;
- an offline report that guides residual modeling, reversible layout, routing,
  dictionaries, or sidecar/SRSTC integration.

Distillation boundary:

```text
teacher/oracle/embedding trace -> deterministic prefix-rebuildable rule -> counted replay
```

A teacher result can choose an experiment. It does not change the score claim
until it becomes a counted decoder component with exact archive, roundtrip,
determinism, memory, and accounting receipts.

## Forbidden Shortcut

Do not treat the embedding model as free compression. If the decoder needs the
model to reconstruct a cluster, feature, or order, then the model or an exact
replacement for it is part of the counted submission payload.

The ledger rule is:

```text
archive_saved_bytes > model_or_rule_bytes + integration_code_bytes
```

For multi-megabyte models, this usually destroys the target unless the archive
gain is also multi-megabyte.

## Candidate Distilled Rules

### SRSTC Loss-Regime Teacher

The older target-closing aggregate SRSTC receipt has a supervised
offline-teacher manifest at
`docs/streaming_retrieval_block_teacher_manifest.jsonl`. It exposes all `4,000`
block offsets, continuous gain labels, and regression labels for the pre-router
shape. The newer block-posterior raw receipt has zero block regressions and
`900,464` net saved bytes, but its unchanged aggregate expert is negative on a
complete fx2 transfer trace. The teacher task has therefore shifted from
explaining raw-shadow block losses to discovering prefix-observable fx2
residual regimes and reversible layout rules.

A Gemma, Doppler, or embedding teacher may read the full labeled block to ask:

```text
which semantic or structural regimes predict SRSTC regret?
which prefix-observable features separate them from weak positive controls?
```

The teacher output is not a router. It must be distilled into a rule using only
the manifest's `512`, `2,048`, or `8,192` byte prefix checkpoints, decoded loss
history, and counted constants. Compare every distilled rule with the
fixed-point block-posterior baseline in
`programs/srstc_raw_order2_aggregate_sketch_blockposterior_v1/`. Reject any
result that needs the block ID, full-block embedding, topic label, or teacher
weights during decode.

### Title Family Key

Rule shape:

```text
family = hash(namespace, lowercase_title_prefix, title_suffix_class)
```

Use:

```text
outer_sse_bucket ^= family & mask
```

Risk: title clusters may be too sparse; use only after held-out shadow proof.

### Template Family Key

Rule shape:

```text
template_family = hash(template_name_prefix, normalized_template_name_shape)
```

Use:

```text
calibrate template argument keys and separators
```

Risk: malformed templates and rare names require abstention.

### Page-Local Schema Trie

Rule shape:

```text
learn keys and reference names only after they are decoded
```

Use:

```text
predict repeated parameter keys, ref names, and URL prefixes
```

Risk: unbounded tries can exceed memory or code discipline; cap nodes and
evict by recency/frequency.

### Embedding-Discovered Ordering Key

Rule shape:

```text
offline embedding suggests deterministic sort key;
decoder reproduces key from decoded page text or counted metadata
```

Use:

```text
improve locality for match models
```

Risk: arbitrary page permutation has a large information cost. Sorting is valid
only if inverse recovery is deterministic or the permutation metadata is
counted.

The first deterministic content-SimHash distillation screen is terminal
negative at the proxy boundary. On the `10,000,000`-byte slice,
`(redirect, category, template, topic, simhash)` scored `5,042.654` adjacency
versus `5,066.252` for the existing geometry key. The broader
`(kind, simhash, shape, size)` key scored `4,256.734`. Because neither beats the
existing proxy, no fx2 compression gate is authorized for these exact keys.
Future embedding teachers must distill a rule that beats geometry on held-out
page families, not merely reproduce a content hash.

- Receipt: `results/page_order_gepa/geometry_simhash_limit10000000.json`

At `100,000,000` bytes, the upstream embedding-order teacher and the direct
locality proxy disagree. Geometry retains stronger teacher neighborhoods than
the highest proxy keys, but the public teacher order itself is weaker than the
geometry forecast. The strongest new proxy key is
`(template, mh2, mh4)`: adjacency `47,804.159` versus geometry `46,608.218`,
while its teacher-neighborhood recall is worse. That conflict authorizes one
exact fx2 archive gate; only real archive bytes can decide between the two
surrogates. No teacher or MinHash payload is credited as compression evidence.

- Proxy receipt: `results/page_order_gepa/geometry_simhash_limit100000000.json`
- Teacher receipt: `results/page_order_gepa/upstream_embedding_teacher_distill_limit100000000_all.json`

That exact target-bearing gate is now terminal negative. On the canonical
`10,000,000`-byte prefix, native arithmetic-coder output reached `1,635,664`
bytes at `94.78%` input coverage, already `2,995` bytes above the
`1,632,669`-byte promotion ceiling before final flush. The run was stopped
without claiming a completed archive, roundtrip, determinism result, or Hutter
score. The monotonic native-output lower bound is sufficient to reject this
ordering shape for the `109,500,000` target, so it does not earn a `100M`
replay. This is direct evidence that the locality proxy did not transfer to the
target-bearing coder threshold.

- Target-ceiling receipt: `results/fx2_gepa_template_mh2_mh4_dictcmix_zlibpy_v1/10m_target_ceiling_abort.json`
- Preserved coder trace: `results/fx2_gepa_template_mh2_mh4_dictcmix_zlibpy_v1/10m_target_ceiling_progress.log`

### Streaming Sketch Retrieval Key

Rule shape:

```text
sketch = simhash(byte_ngrams, token_minhash, schema_state, suffix_bytes)
```

Use:

```text
retrieve similar prior chunks and mix their following bytes as a soft probability
```

Risk: the sketch must be integer deterministic and history-derived. The final
decoder may not ship an embedding index or depend on floating-point cosine
similarity.

## Acceptance Rule

Every distilled rule needs a receipt:

```text
teacher_artifact: offline only
distilled_rule_bytes: counted
integration_code_bytes: counted
shadow_or_driver_saved_bytes: measured
net_saved_bytes: saved - counted
```

If the decoder cannot recompute the rule from history and counted constants,
the rule is not valid for the final archive.
