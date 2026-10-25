# Linked102-document CPU evaluation successor — not launched

This separate version preserves all original54-document code, caches and results.
It is prepared for main's independent exact-freeze review and native execution
authority. Preparation and synthetic tests are not permission to run the model.

## Attribution-safe three-arm design

| Arm | Document representation | Metadata/qualification service | Purpose |
|---|---|---|---|
| historical reproduction | original54 enriched +4027 titles | pinned historical v8 | Reproduce stored historical decisions/metrics exactly |
| matched availability control | same original54 representation/vectors | pinned v16 | Measure service-availability change alone |
| expanded document arm | 102 enriched +3979 titles | the **same pinned v16** | Measure document change versus matched control |

The document-effect delta is **102/v16 minus54/v16**. The service-only delta is
**54/v16 minus54/v8**, reported separately for every policy. Neither is mislabeled
as the other. No combined service-plus-document gain is attributed solely to
better semantic representation. Same20 cosine/margin policies and existing policy
selection criterion are used in each arm; no additional thresholds or guard edits.
All4,081 competitors are ranked, with no availability filter or runner-up fallback.
Stored metadata qualification is not query-public execution verification.

## Only48 new document encodes

The frozen expansion supplies102 lawful authoritative descriptions. Its old54
semantic text bytes and all original competitor IDs/order were checked unchanged.
The runner again live-gates54/102 statement IDs immediately before each combined
document artifact read and validates per-document text SHA and plan identity.
Only the48 newly enriched rows reach `encoder.encode`, in12 batches of4 with
`query=False`. Any truncation blocks comparison. Each batch emits an fsynced
NumPy array, SHA-bound receipt and progress record; a failure preserves these
partial artifacts. Runs use a new output directory—no ambiguous partial-cache
reuse. No query is re-encoded.

Existing caches reconstruct the exact original4,081 index: original54 enriched
vectors and4027 title vectors. Replacement touches only the48 changed positions.
The original54 enriched vectors and3979 remaining title vectors are asserted
byte-value identical after replacement. All52 query vectors are reused with full
text/order/encoder/binding/array hash and truncation checks. Truncated queries or
index documents cannot enter the completed comparison. The historical54/v8
status/reason/identity/exactimplementation decisions and metrics must reproduce
before new results are emitted.

## Exact runtime and budgets

Reuse existing pinned CPU assets/private venv only: model/tokenizer and auxiliary
manifest hashes, runtime/interpreter hash, package versions, encoder adapter,
query instruction, last-token L2 pooling, float32, left padding,1024 token limit,
2 CPU threads,1 interop thread, batch4. No downloads, training, GPU use, model
replacement, query-vector regeneration, candidate source reads or execution.
Confirmation remains sealed.

8 GiB address space;300 CPU seconds soft/305 hard;240 seconds wall; at least5 GiB
effective memory headroom. The signal-safe supervisor is derived from the reviewed
persistent-timing supervisor: owned new session, handled/restored signals,
whole-group TERM/KILL cleanup and observed absence of executing group members.
Terminal failure manifests preserve interruption/error scope; raw source and query
text are not exported in comparison decisions.

This measures a **cached development representation iteration**, not cold complete
index-building cost or fresh-serving latency. Historical cache/model work remains
charged separately in predecessor evidence; cache reuse does not erase that cost.
The52 authored examples remain non-IID development data, not confirmation or a
population risk certificate. No result automatically qualifies recognition.

## Preparation evidence

12 synthetic tests pass: full alignment, old54 preservation, all-vector retention,
exact48 `query=False` fake-encoder calls, incremental cache output, truncation and
binding rejection, pre-open gate denial, historical reproduction, fixed20 policies,
and a deliberate service-improvement/document-regression fixture proving separate
attribution. Tests load only owned synthetic NumPy arrays, never actual encoder
weights or candidate programs. Preparation hashes existing caches but does not
load their arrays or score a cohort.

## After independent approval only

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/shared/deco/gamma \
/usr/bin/python3 projects/algorithm_solver/catalogue/description-enriched102-v1/launch.py \
  --freeze /workspace/shared/deco/gamma/projects/algorithm_solver/catalogue/description-enriched102-v1/freeze.json \
  --freeze-sha256 REVIEWED_SHA256 --output NEW_PRIVATE_OUTPUT_DIRECTORY
```

The main results are `results/report.json`, `results/documents-cache/`,
`results/progress.json`, and the supervisor/optional failure manifests. Every
policy reports historical, matched-control and expanded-arm metrics and compact
decisions; selected policies are reported separately, without confirmation access.
