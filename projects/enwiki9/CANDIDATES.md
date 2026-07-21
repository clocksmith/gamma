# enwiki9 Candidate Organization

This project treats every compressor attempt as a candidate program with a
tracked source contract, tracked metadata, and measured evidence. The goal is to
make the candidate pool ready for open-ended search without allowing abandoned
or undocumented experiments to pollute the active set.

For the broader project ownership map, active proof lane, and document routing,
see `PROJECT_ORGANIZATION.md`. This file owns candidate lifecycle and evidence
rules; it does not own the live cmix21 promotion queue or final proof claim.

## Directory Contract

Active candidates live under:

```text
projects/enwiki9/programs/<candidate_id>/
```

Every active candidate must have:

- `program.py`: defines `compress(data: bytes) -> bytes` and `decompress(data: bytes) -> bytes`.
- `meta.json`: declares the candidate identity, provenance, dependencies, and genotype hints.
- An entry in `index.json`.
- At least one valid roundtrip result before it can be used as training signal for search.

Generated and local-only artifacts stay outside the tracked candidate contract:

- `projects/enwiki9/data/enwik9`
- `projects/enwiki9/data/enwik9.zip`
- `projects/enwiki9/build/`
- `projects/enwiki9/results/`
- `__pycache__/`

Benchmark evidence is summarized in tracked reports and inventories instead of
tracking every generated result file.

## External Source Boundary

External compressor code must not remain as an undocumented untracked checkout.
Use one of these boundaries:

- Direct vendoring: track the raw source files in the parent repository.
- Submodule: track a fetchable commit through `.gitmodules`.
- Patch overlay: track the upstream commit plus a patch file that reconstructs
  local modifications.

`external/fx2-cmix/` currently uses the patch overlay boundary:

- `external/fx2-cmix.vendor.json` records upstream provenance.
- `external/fx2-cmix.local.patch` records local source modifications.

This is a non-destructive holding pattern. It preserves local changes while
leaving the nested checkout metadata intact. Convert it to direct vendoring only
after deciding that the parent repository should own every raw `fx2-cmix` file.

## Lifecycle

| State | Meaning | Required action |
|---|---|---|
| `draft` | Source exists but the contract is incomplete. | Add metadata and registry entry, or retire it. |
| `candidate` | Contract is complete but benchmark evidence is missing. | Run a same-scope roundtrip benchmark. |
| `active` | Contract is complete and valid measured evidence exists. | Eligible for search and crossover. |
| `measured_negative` | Valid roundtrip loses on score but preserves distinct mechanism evidence. | Keep as evidence; do not use as a winner. |
| `blocked_dependency` | Contract exists but the local substrate is missing or broken. | Fix dependency or retire. |
| `track_source_before_evolution` | Source exists outside the safe Git boundary. | Track or document source boundary before scoring. |
| `retired` | Contract fails, roundtrip fails, or measured value is absent after audit. | Keep only if documented as a negative result. |

## Evidence Basis

Do not mix exact measurements with inherited or forecast frontier claims.

- `measured`: exact `lib/driver.py` or equivalent same-scope result. It must
  include `data_size`, archive bytes, counted program bytes, total S, roundtrip
  status, and determinism status when available.
- `inferred_frontier`: inherited or forecast rows. These may use measured
  archive identity, measured program-size deltas, or calibrated full-corpus
  forecasts, but they are not driver results at that scope.
- `requires_driver_confirmation`: true whenever an inferred row is still
  waiting for an exact same-scope run.

Packaging wins and model wins must be described separately. If archive bytes do
not improve, the row is a container/program-size win, not an algorithmic
compression improvement.

`candidate_audit.py` accepts both saved result JSON files and structured
metadata evidence in `meta.json`. A metadata-backed gate must include a concrete
scope, archive bytes, counted program bytes or total S, and either direct
roundtrip/determinism fields or an inherited identity basis. Unstructured notes
do not count as valid evidence.

For target accounting, run:

```bash
python3 projects/enwiki9/tools/frontier_target_report.py --target-percent 10.95
```

The report ranks total projected `S = archive + program_size` and separates
evidence quality: exact 1G, fx2-calibrated from exact 100M, fx2-calibrated from
10M, generic forecasts, and speculative sub-10M extrapolations. A target hit is
not a submission claim until an exact same-scope driver result confirms it.
Treat any 10M-calibrated target hit as a screening lead, especially when small
sub-1M gates are mixed with inherited 10M metadata. Those rows choose the next
locked experiment; they do not prove full-corpus performance.

## Lane 0 Evidence Hygiene

Lane 0 is the shared intake gate for the existing cleanup queue and every new
Lane B candidate. It answers one question before a program can become a parent,
control, or frontier point: does the candidate have a complete contract and
valid same-scope evidence?

Use the dry-run view first:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --limit-candidates 10
```

The dry-run reads `candidate_inventory.json`, selects `benchmark_or_retire`
candidates by default, and prints the locked gate plan. It does not score or
write metadata.

Before spending the scorer lock, contract-only cleanup can validate the
`program.py` API without compression:

```bash
python3 projects/enwiki9/tools/candidate_triage.py \
  --contract-check \
  --status benchmark_or_retire
```

This check imports `program.py` in an isolated subprocess, matching
`lib/driver.py` loader semantics. Do not replace this with AST-only inspection:
many compact wrappers expose `compress` and `decompress` by unpacking a payload
at import. To repair a false retired status after a loader change:

```bash
python3 projects/enwiki9/tools/candidate_triage.py \
  --contract-check \
  --update-meta \
  --restore-ok-status benchmark_or_retire \
  --candidate <candidate_id>
```

Scoring requires an explicit bounded run:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --run --limit-candidates 1
```

To let the script update each candidate's `meta.json` with `lane0_triage`
measurements and a proposed lifecycle status:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --run --update-meta --limit-candidates 1
```

When comparing against a baseline that already has deterministic same-scope
evidence in result JSON or `meta.json`, add:

```bash
python3 projects/enwiki9/tools/candidate_triage.py \
  --run \
  --update-meta \
  --reuse-baseline-evidence \
  --baseline fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1 \
  --candidate <candidate_id>
```

By default the script runs each `lib/driver.py` gate without heavy-lock gating.
Use `--respect-heavy-lock` to require this extra serialization.

Default gates are:

- 1 KiB deterministic roundtrip against `baseline_lzma`.
- 250000-byte deterministic roundtrip against the same baseline.

Outcomes:

- Import, contract, roundtrip, or determinism failure: `retired`.
- Missing local substrate: `blocked_dependency`.
- Busy scoring slot: stop without changing candidate status.
- Valid deterministic score win: `active`.
- Valid deterministic loser with useful evidence: `measured_negative`.

This is the pruning path for the `benchmark_or_retire` queue. It should run
before any naming cleanup. Renaming should only touch candidates that Lane 0 has
classified as `active`, `measured_negative`, or explicitly useful controls.

Current `benchmark_or_retire` cleanup should be consumed in mechanism groups:

- `typed_opcode_custom`: opcode/typed-anchor candidates first, because they feed
  Lane B structural-state extraction.
- `schema_xml_title_lzma`: schema, title, and XML skeleton wrappers next,
  because they are direct macro-residual controls.
- `named_custom_family`: yellow_tucan and related standalone families, grouped
  by shared mechanism.
- `fx2_cmix_or_sidecar`: leave lock-heavy fx2/cmix wrappers to Lane A unless
  Lane A explicitly asks for a cleanup gate.
- `baseline_backend`: backend controls last.

The latest contract-only sweep found the remaining `benchmark_or_retire`
wrappers import cleanly and expose both required callables. They still need
locked roundtrip evidence before status changes.

Exact gates launched manually with `lib/driver.py` can be folded into a
candidate contract without another benchmark run:

```bash
python3 projects/enwiki9/tools/record_driver_result.py <candidate_id> \
  --label 1m_driver_gate \
  --status active \
  --verdict "Archive-positive exact 1M gate; promote to larger-scope screen."
```

## Lane B Core Tuning

Core tuning candidates mutate the rebuilt `fx2-cmix` predictor rather than the
outer wrapper. The current compile-time knobs are:

- `FX2_MIXER_CONTEXT_LIMIT`: maximum learned contexts per mixer before falling
  back to the shared base context.
- `FX2_MIXER0_LR_SCALE`: layer-0 mixer learning-rate multiplier.
- `FX2_MIXER1_LR_SCALE`: layer-1 mixer learning-rate multiplier.
- `FX2_LSTM_LR_SCALE`: byte-mixer LSTM learning-rate multiplier.
- `FX2_SSE_WR_SCALE_PPM`: integer parts-per-thousand scale for SSE write rates.

## Residual Certificate Lane

Residual candidates are only worth packaging after they satisfy a certificate
gate. The target against the current calibrated production path is:

```text
required_net_gain = 681,114 bytes = 5,448,912 bits
```

Use this order:

1. Emit `FX2_RESIDUAL_ROW` traces from an unchanged-byte `fx2` run.
2. Run an oracle upper-bound scan for the proposed structural state family.
3. If the oracle cannot clear the target after code/table cost, prune that state
   family as `measured_negative` evidence.
4. If the oracle can clear the target, build a causal extractor and score exact
   residual gain with `fx2_residual_gain_certificate.py` or the shadow coder.
5. Package a decompressor candidate only after the causal extractor satisfies:

```text
residual_gain_bits - added_code_bits >= 5,448,912
```

The first tested KT/APM coupling over `p_bucket,bit_pos,*` states is pruned from
active search. It remains documented in `RESIDUAL_CERTIFICATE_REPORT.md`.

Use the package helper to build a normal candidate directory from those knobs:

```bash
python3 projects/enwiki9/tools/fx2_core_tune_package.py \
  --id fx2_core_tune_title_mctx20k_m0p95_m1p105_sse950_v1 \
  --mixer-context-limit 20000 \
  --mixer0-lr-scale 0.95 \
  --mixer1-lr-scale 1.05 \
  --sse-wr-scale-ppm 950 \
  --compiler g++
```

The helper packages the tuned binary into the title-order wrapper template. It
does not benchmark or promote the candidate. After creation, register and gate
it through Lane 0 under `/tmp/enwiki9-heavy.lock`.

Core-tuning promotion is archive-first:

- Same-scope archive bytes must improve against the parent/control.
- Any program-size increase must be counted in `S`.
- Gains must hold when moving from the small gate to the next larger gate.
- Deterministic roundtrip is mandatory.

## Lane B Hybrid GEPA Ordering

GEPA page-order work is a selector pipeline, not a score by itself. The hybrid
screen combines deterministic feature enumeration with random mutation,
crossover, and diversity selection over reversible order keys:

```bash
python3 projects/enwiki9/tools/page_order_gepa_hybrid.py \
  --limit 10000000 \
  --max-candidates 8000 \
  --top 60
```

The screen does not run `cmix`, `xz`, `lzma`, `bench.py`, or `lib/driver.py`.
It ranks page-order genotypes using model-free adjacency continuity, so this
work is safe while `/tmp/enwiki9-heavy.lock` is held by another scorer.

Promising genotypes become self-contained candidates through:

```bash
python3 projects/enwiki9/tools/fx2_gepa_order_package.py \
  --id fx2_gepa_template_topic_mh4_shape_dictcmix_zlibpy_v1 \
  --fields kind,template,topic,mh4,shape \
  --screen-json projects/enwiki9/results/page_order_gepa/hybrid_limit10000000_seed271828.json
```

The package helper copies the counted backend assets and writes the reversible
order key into the candidate payload. Register and gate the candidate through
Lane 0 before promotion. GEPA screen rank is only admission evidence for exact
measurement; it is never a Hutter score.

## Retire Criteria

Retire or repair a candidate when any of these are true:

- `program.py` is missing.
- `meta.json` is missing or its `id` does not match the directory name.
- The candidate is absent from `index.json`.
- Source files are untracked.
- No valid roundtrip evidence exists after an explicit benchmark or structured
  inherited-identity proof.
- It duplicates another candidate without a measured improvement or a distinct mechanism.

Deletion is not the first step. First classify the candidate, preserve useful
negative evidence in documentation, then remove or move the source only when the
audit has a concrete reason.

## PGSG Mapping

The Polymorphic Graph-Schema Genotype (PGSG) layer maps each compressor attempt
onto a DAG-like candidate schema:

- Nodes represent functional units: parser, transform, sort, sidecar, entropy
  model, backend codec, dictionary, or parameter controller.
- Edges represent byte streams, token streams, sidecars, receipts, dictionaries,
  or execution dependencies.
- Payloads carry continuous parameters, discrete options, and structural
  subgraphs.

Recommended `meta.json` extension:

```json
{
  "id": "example_candidate_v1",
  "description": "short mechanism description",
  "added": "2026-06-07",
  "deps": [],
  "status": "candidate",
  "family": "fx2_sidecar",
  "pgsg": {
    "nodes": [
      {
        "id": "preprocess",
        "type": "transform",
        "payload": {
          "discrete": {"mode": "byte_split"},
          "continuous": {},
          "structural": {}
        }
      },
      {
        "id": "backend",
        "type": "codec",
        "payload": {
          "discrete": {"codec": "xz"},
          "continuous": {"preset": 9},
          "structural": {}
        }
      }
    ],
    "edges": [
      {"from": "preprocess", "to": "backend", "stream": "payload"}
    ]
  }
}
```

The PGSG block is descriptive until the search runner consumes it. The audit
tool does not require it yet, but every new candidate should include enough
family and mechanism metadata to let a future graph search compare structure
rather than just directory names.

## Lane B Intake

Lane B is reserved for novel mechanisms such as macro-residual edit scripts,
layout grammar templates, page-order selectors, VM-trace sidecars, and online
prefix dictionaries. Each new Lane B program starts with:

- `status: "candidate"`
- a complete `program.py`/`meta.json` contract
- a `pgsg` block that names the mechanism and backend
- registration in `index.json`

After creation, Lane B candidates use Lane 0 triage before promotion:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --candidate <id>
python3 projects/enwiki9/tools/candidate_triage.py --run --update-meta --candidate <id>
```

Only `active` or `measured_negative` Lane B outputs should become named
frontier points or parents for later search.

### Typed-Anchor Handoff

`opcode_typed_anchor_bitmix_v1` is the strongest current Lane B structural
signal. Its standalone archive beats `baseline_lzma` at the 1M gate, but it is
not an fx2-class backend. Treat it as a state extractor, not as a replacement
compressor. The evidence says the extractor has real density; it does not say
the rewritten opcode stream should be fed to fx2.

Generate the Lane A handoff report with:

```bash
python3 projects/enwiki9/tools/typed_anchor_signal_report.py --limit 1000000
```

The report writes:

```text
projects/enwiki9/lane_b_typed_anchor_handoff.json
```

It records both streams:

- `opcode_stream_state`: the state shape used by the standalone physical opcode
  preprocessor.
- `raw_stream_state`: the state shape Lane A should prefer when porting to fx2,
  because fx2 should preserve the original byte stream.

Port only the compact soft state: field, wiki mode, slot, page kind, byte
class, and column bucket. Do not port the physical opcode rewrite, hard context
XORs, chain-copy opcodes, or direct final-probability clamps. The first fx2
candidate is `fx2_typed_anchor_soft_sse_v1`: a narrow SSE/APM-side coordinate
keyed by prediction bucket, bit position, field, and slot. Promotion is based
on archive-byte improvement against the same fx2 parent at matching scope.

Build the first candidate package after Lane A releases the scorer:

```bash
python3 projects/enwiki9/tools/fx2_core_tune_package.py \
  --id fx2_typed_anchor_soft_sse_v1 \
  --mixer-context-limit 8000 \
  --mixer0-lr-scale 1.0 \
  --mixer1-lr-scale 0.95 \
  --lstm-lr-scale 1.0 \
  --sse-wr-scale-ppm 1000 \
  --mixer-decay-t0 500000 \
  --mixer-decay-t1 3000000 \
  --mixer-decay-t2 16000000 \
  --mixer-decay-p0 1000000 \
  --mixer-decay-p1 600000 \
  --mixer-decay-p2 250000 \
  --mixer-decay-p3 125000 \
  --typed-anchor-soft-sse \
  --typed-anchor-soft-sse-weight 0.0002
```

This compiles `FX2_STRUCT_SIDECAR=5`, which updates raw-stream state without
activating the older hard context mutations or broad sidecar mixer set.

To build and gate this family through the standard locked promotion path, use:

```bash
python3 projects/enwiki9/tools/fx2_typed_anchor_soft_queue.py \
  --run \
  --gate-size 1024 \
  --gate-size 250000 \
  --gate-size 1000000 \
  --archive-ceiling 250000:<same-parent-250k-archive> \
  --archive-ceiling 1000000:<same-parent-1m-archive>
```

Explicit mutations use:

```text
--spec ID:WEIGHT
--spec ID:WEIGHT:MODE
--spec ID:WEIGHT:MODE:MCTX:M0:M1:LSTM:SSEPPM:T0:T1:T2:P0:P1:P2:P3
```

The queue always passes `--typed-anchor-soft-sse`; it is not a route for the
physical opcode rewrite.

### Shadow Residual-Coder Certificate

Do not promote new structural side-state by intuition. The stronger proof path
is an exact shadow arithmetic certificate:

```bash
python3 projects/enwiki9/tools/fx2_shadow_residual_coder.py \
  <fx2_residual_log> \
  --key p_bucket,bit_pos,field,mode \
  --fx2-decoder-bytes <counted_decoder_bytes> \
  --patch-bytes <parser_and_coder_patch_bytes> \
  --print-summary
```

This consumes per-bit fx2 residual rows containing `bit` and `p1`. If a row has
`corrected_p1`, that exact probability is encoded. Otherwise the tool builds a
tiny causal KT table keyed by the requested state and blends it with fx2's
probability. The table updates only after the current bit is encoded, so the
model is decoder-realizable.

The certificate theorem is:

```text
S_new <= |D_fx2| + |D_patch| + exact_shadow_arithmetic_bytes
```

`fx2_residual_gain_certificate.py` remains useful for log-loss screening.
`fx2_shadow_residual_coder.py` is stricter: it includes integer probability
quantization, coder finalization overhead, cold-start cost, and finite decoder
byte accounting. It labels a 10.95 result constructive only when the trace
covers the asserted target stream and decoder bytes are supplied.

### Manifold Outer SSE Search

The current structural route is `fx2__manifold_outer_sse__sphere_torus_residual__v01`.
It treats stochastic search as an offline discovery step only. The online
candidate must collapse to a fixed-point integer projection and a tiny causal
outer SSE/APM table keyed by:

```text
p_bucket,bit_pos,manifold_bucket
```

Generate raw residual rows with `FX2_RESIDUAL_LOG=1` and
`FX2_STRUCT_SIDECAR=1`. The residual logger now emits causal page-manifold
fields including `page_bucket`, `category_state`, `template_arg`,
`link_recency`, `title_hash`, `template_hash`, `link_hash`, `entity_hash`,
`word_hash`, and `pair_sig`. These are observational only; they must not alter
baseline archive bytes.

Run the offline projection search with:

```bash
python3 projects/enwiki9/tools/fx2_manifold_outer_sse_search.py \
  <fx2_stderr_residual_log> \
  --output projects/enwiki9/results/fx2_manifold_outer_sse/search.json \
  --train-bytes <heldout_start_byte> \
  --trials 32 \
  --sphere-bins 4,8 \
  --torus-bins 4,8 \
  --pos-shifts 8,10,12 \
  --blend-ppm 25000,50000,125000 \
  --shadow-top 3 \
  --print-summary
```

Promote only if exact shadow arithmetic, not just log-loss, shows enough
out-of-sample slope to plausibly pay:

```text
archive_saved - program_added >= 681114 bytes
```

Current evidence from `manifold_rich_64k_v1` is negative for the first
KT/APM-style manifold form. The rich logger emitted the intended causal fields,
and the focused split search found a tiny held-out qbit gain, but exact shadow
arithmetic lost bytes:

```text
trace: projects/enwiki9/results/fx2_residual_probe/manifold_rich_64k_v1/stderr.log
search: projects/enwiki9/results/fx2_residual_probe/manifold_rich_64k_v1/manifold_outer_sse_search_heldout_shadow.json
rows: 120000
best held-out proxy gain: 1.033203125 bytes
exact full-prefix shadow result: baseline 5616 bytes, shadow 5620 bytes, net -4 bytes
exact held-out shadow result: baseline 2720 bytes, shadow 2719 bytes, net +1 byte
```

Do not package this projection. Its post-warm-up slope is real but too small:
6 held-out bits across 54464 held-out rows is below the 10.95 requirement. The
usable result is the apparatus: richer causal residual logging, fixed-point
manifold projection search, exact shadow arithmetic, held-out shadow reranking,
and a dormant C++ hook. The next manifold attempt must optimize against exact
shadow bytes directly or use a different correction form.

The residual-bias correction is stronger than KT because it preserves fx2's
base probability and learns only the signed residual. Low-cardinality bias
search is exact-positive, but still too weak:

```text
search: projects/enwiki9/results/fx2_residual_probe/manifold_rich_64k_v1/manifold_outer_sse_search_bias_lowcard_full64k.json
rows: 301808
best exact full-prefix result: +62 bits
best exact held-out result: +3 bits over 39664 held-out rows
status: apparatus-positive, not candidate-positive
```

The C++ hook supports this form with `FX2_MANIFOLD_CORRECTION_BIAS=1`, and the
package helper exposes it as:

```bash
python3 projects/enwiki9/tools/fx2_core_tune_package.py \
  --id fx2__manifold_outer_sse__lowcard_bias__v01 \
  --manifold-outer-sse \
  --manifold-correction bias \
  --manifold-p-buckets 16 \
  --manifold-sphere-bins 4 \
  --manifold-torus-bins 4 \
  --manifold-blend-ppm 50000
```

Do not gate that package until a larger residual trace shows target-scale
exact shadow slope. The current signal projects below the 681114-byte debt.

Typed-anchor context modes are:

- `0`: prediction bucket, bit context, field, slot
- `1`: prediction bucket, bit context, field, XML/wiki mode
- `2`: prediction bucket, bit context, word-length bucket, byte class
- `3`: prediction bucket, bit context, field, word-length bucket, byte class
- `4`: compact combined field, slot, mode, page kind, byte class, column bucket
- `5`: prediction bucket, bit context, field only
- `6`: prediction bucket, bit context, XML/wiki mode only

Prefer modes `6` and `5` before retesting combined states. The first soft-SSE
pass showed that combined typed-anchor coordinates can be valid and
deterministic while still missing archive ceilings; isolated states test whether
the signal survives without fragmenting the parent model.

### Projection Rule

Treat enwik9 as structured data projected onto a flat byte stream. Do not split
primary model history with hard context mutations unless the archive bytes prove
the split is worth the lost continuity. Prefer transformations that preserve
the original stream or derive state from bytes already visible to both encoder
and decoder:

- Static or learned residual streams must be reversible and byte-exact.
- Page or layout reordering must carry explicit order cost in the archive.
- Mixer side state should be additive or softly gated, not a destructive hash
  replacement.
- Every extra coordinate system must pay for its counted source bytes at the
  same data scope.

### Macro-Residual Token Search

Static macro tables saturate at small table sizes, so token additions must be measured
instead of guessed. Use the locked helper against a parent program that exposes
its byte macro list as `S`:

```bash
python3 projects/enwiki9/tools/macro_token_search.py \
  --parent xml_scaffold__macro_residual__wiki_layout__lzma_extreme__min__v03 \
  --limit 1000000 \
  --greedy
```

The helper acquires `/tmp/enwiki9-heavy.lock` before running LZMA evaluations.
Rows are sorted by estimated net score delta (`archive_delta +
source_cost_hint`). Greedy mode re-evaluates remaining tokens after each
accepted addition so interacting tokens are measured against the updated table.
Only tokens whose archive savings exceed their added source bytes should become
a new candidate table.

## Audit Command

Run:

```bash
python3 projects/enwiki9/tools/candidate_audit.py --write
```

This refreshes:

- `projects/enwiki9/candidate_inventory.json`
- `projects/enwiki9/CANDIDATE_INVENTORY.md`

Use the inventory before staging or deleting candidates. The action list tells
you which candidates are active, which need benchmark evidence, which have
untracked source, and which should be retired or repaired.
