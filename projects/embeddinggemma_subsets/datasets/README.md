# Datasets

Per-language eval sets live under `datasets/<lang>/dataset.json`.

Format:

```json
{
  "queries": ["..."],
  "docs": ["..."],
  "relevant": [[query_index, doc_index], ...]
}
```

Notes:
- Keep these small but meaningful. The goal is regression detection, not leaderboard performance.
- Prefer 50-500 queries per language as the set grows.
- `relevant` may include multiple docs per query (multiple pairs with the same `query_index`).

