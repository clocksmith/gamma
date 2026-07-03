# Embedding-Teacher Rule Distillation

Embedding models can help `enwik9` only as offline teachers unless their full
artifact bytes are counted and beaten. The final Hutter decompressor should
ship tiny deterministic rules, not a large embedding model.

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
- an offline report that guides cmix21 memory shaping.

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
