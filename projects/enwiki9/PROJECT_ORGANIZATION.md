# enwiki9 Project Organization

This file is the ownership map for the `enwiki9` compression project. It
defines where strategy, algorithms, evidence, tools, and submission accounting
belong so the project does not drift back into scattered notes.

## Current Operating Thesis

The project has one proof objective:

```text
full enwik9 official score <= 109,500,000 bytes
```

The project currently has no full-corpus constructive proof at that target. A
counted heterogeneous-recurrent cumulative-`10M` backend screen and exact
source-wrapper replay are terminal, but neither can prove the target. The unchanged
`cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
package is economically retired: its exact `100M` first archive was
`14,864,716` bytes, which missed the unified-executable promotion screen by
`149,143` bytes, so it must not advance to `1G`.

The original-order archive-neutral `CMIX21F3` trace is terminal, and its large
full-teacher complement is not additive to the constructive geometry `96x2`
candidate. The corrected matched-geometry opening experiment retained only
`290 B/1M` overall and `355 B/1M` on internal holdout. The frozen blend then
retained only `61 B/1M` on an offset-`500M` same-store slice, versus the
repackaged base's `252.737 B/1M` debt before integration. Family averages,
individual layer-0 outputs, continuous 160/200-cell probes, the full final
endpoint, and the measured contextual maps are retired as add-on experts in
their measured forms. Separately, the standalone PAQ-free
`200x2` codec has an exact first-`1M` archive of `174,055` and saves
`1,149 B/1M`, but the frozen offset-`500M` reset slice retains only
`370 B/1M` against its source-accounted `762.424 B/1M` floor. It is retired
without replay or a larger unchanged gate. The lower-cost heterogeneous `112+80`
construction saves `1,084 B/1M` at the first `1M` and `795.6 B/1M`
cumulatively at `10M`. Its `1,635,670`-byte archive misses deflate-ZIP
accounting by `37` bytes. A reproducible `264,646`-byte direct-entry bzip2 ZIP
reconstructs all `77` source files and clean-builds twice to the exact
wrapper-proven program, saving `23,619` counted bytes over the prior selected
package. The selected linear forecast is `109,467,156`; applying the same
package saving to the `1M`-to-`10M` tail forecast gives `109,498,879`.
The wrapper passes identity, roundtrip, determinism, and RSS. On the matched
offset-`500M` reset slice, however, `112+80` saves only `353 B/1M` total and
only `4 B/1M` over native `112`; it is retired from promotion. Raw-order SRSTC
shadow saving remains non-additive evidence. The explicit command-costed WRT
phrase-copy macro has now been tested: all `432` active development
configurations lose bytes, so its frozen holdout action is abstention. Do not
duplicate that endpoint shape.

The active construction gate is instead a matched original-order replacement.
On the archive-identical exact FX2 stream, a fixed compact-`200` blend saves
`1,345 B/1M` overall and `1,325 B/1M` on internal holdout with zero block
regressions and exact range-decoder replay. This cannot be added to the geometry
forecast: original order gives back `506.4 B/1M` at the exact `10M` FX2
boundary, and the separately evolved predictors do not yet establish a counted
combined program or memory bound. The `750000`-ppm blend is frozen for
cumulative `10M`; a pass advances only to one-process shared-state integration.

Fixed `96x2` now has a reproducible `264,427`-byte source package that
clean-builds twice to the exact backend and wrapper. This lowers its
cumulative-tail forecast debt to `252,737` bytes. The package authorized one
frozen disjoint test of the already replayable fixed full-CMIX complement; the
measured `61 B/1M` result retires that complement without native integration or
a larger gate. Receipt:
`results/fx2_cmix21_matched_disjoint_terminal_v1/receipt.json`.

The older structural concepts are not discarded. They become backup lanes,
baselines, SRSTC components, or offline-teacher discovery tools until exact
receipts show that one should be promoted.

## Source Of Truth Map

| Question | Source of truth | What belongs there |
|---|---|---|
| What is the project and how are results reported? | `README.md` | Scoring math, result JSON fields, scope discipline, reporting vocabulary. |
| What algorithms exist and what evidence do they have? | `ALGORITHMS.md` | Mechanism explanations, measured rows, current strategy register, paper/design note index. |
| How can a reader orient on the main algorithms? | `docs/algorithm_cards.md` | Plain-English cards: mechanism, score, proof boundary, next role. |
| What are the canonical per-run stored records? | `results/run_ledger.jsonl` | Append-only run registry with `run_id`, timing, memory snapshots, determinism, and result-pointer fields. |
| What artifact-backed rows currently rank best by scope? | `docs/evidence_matrix.md` | Generated score/archive matrix from result JSONs only; no forecasts or inherited metadata. |
| What are the top rows without the full evidence matrix? | `docs/best_results.md` | Generated compact top-three score/archive rows for selected measured scopes. |
| What is the current one-page operator status? | `docs/status_receipt.md` and `docs/status_receipt.json` | Generated target state, lock state, active RSS, gate decision, and proof boundary. |
| What candidate folders are valid or retired? | `CANDIDATES.md` | Candidate contract, lifecycle, evidence basis, retirement rules, audit commands. |
| What is the generated candidate audit snapshot? | `CANDIDATE_INVENTORY.md` and `candidate_inventory.json` | Generated inventory and status counts. Do not hand-edit generated facts. |
| What is the source-bound frontier ledger? | `docs/hutter_run_ledger.json` and `docs/hutter_run_ledger.md` | Candidate-run frontier rows with measured scope, evidence tier, forecast fields, proof/disqualifier states, and source-pointer assertions. |
| What is the current cmix21 execution queue? | `CMIX21_LOCK_SAFE_QUEUE.md` | Active memory-valve candidates, lock-safe gates, memory-value table, promotion posture. |
| What does the measured PPMD memory-valve ladder show? | `docs/cmix21_memory_valves.md` | Generated cmix21 cap ladder, 10M archive deltas, and recorded RSS outcomes. |
| What non-PPMD cmix21 memory surfaces have evidence? | `docs/cmix21_memory_surfaces.md` | Generated scan of PAQ, FXCM-RCM, RCM, buffer, guard, and match-token evidence from saved receipts. |
| Has anything proven the target? | `UPPER_BOUND_CERTIFICATE.md` and `upper_bound_certificate.json` | Exact constructive proof state and best exact bounds by scope. |
| What is the main novel sidecar architecture? | `FX2_SC.md` and `FX2_SC_PAPER.md` | Non-destructive structural/cognitive context mixing design and rollout. |
| What residual/SSE proof work exists? | `RESIDUAL_CERTIFICATE_REPORT.md`, `RESIDUAL_ROUTER_LOCK_SAFE_REPORT.md`, `docs/shadow_coder_spec.md`, `docs/residual_shadow_matrix.md` | Residual proof reports, generated cached shadow matrix, negative evidence, required trace schema. |
| What is the primary novel strategy? | `docs/streaming_retrieval_mixer.md` | Generated SRSTC algorithm, determinism contract, receipt schema, implementation queue, and kill gates for causal self-referential semantic retrieval. |
| Which SRSTC receipts are actually promotable? | `docs/streaming_retrieval_receipt_audit.md` and `docs/streaming_retrieval_receipt_audit.json` | Conservative audit of held-out net savings, alignment safety, online state bounds, and complete block-regression evidence. |
| What corpus regimes explain the SRSTC regressions? | `docs/streaming_retrieval_block_regime_audit.md` and `docs/streaming_retrieval_block_regime_audit.json` | Offline teacher-only labels and weak-positive controls; only the causal prefix checkpoints may seed a final distilled rule. |
| How could offline teachers and decoder-rebuilt retrieval close the target debt? | `docs/offline_teacher_retrieval_investigation.md` | Target-debt math, admissible embedding-teacher use, deterministic rule/dictionary/routing/retrieval lanes, and proof gates for counted replay. |
| Does the current search follow Gamma's latest SAME-R strategy? | `docs/same_r_hutter_strategy_audit.md` | Matched-evaluation audit, exact-codelength controls, oracle-economics gates, candidate-universe saturation, mechanism priorities, and missing constructive evidence. |
| What did the PAQ-free FX2/CMIX21 LSTM frontier prove? | `docs/fx2_cmix21_nopaq_lstm_frontier.md` | Exact first-`1M` constructive evidence, cumulative `10M` economics, runtime/RSS frontier, counted package boundary, retirement reason, and the conditional-endpoint next gate. |
| What did the matched CMIX21/96x2 endpoint screen prove? | `docs/cmix21_fx2_family_trace_correction.md` | The original-order basis mismatch, constant FXCM/PAQ trace bug, archive-neutral geometry correction, exact `290 B/1M` replay, and current endpoint-universe retirement boundary. |
| What evidence level does a teacher, shadow, prefix, block, or full replay prove? | `ALGORITHMS.md` and `docs/research_register.md` | Five-level evidence ladder separating proxy forecasts, target-substrate shadows, counted prefix receipts, disjoint block receipts, and full official score claims. |
| Where are strategy and novel-algorithm research lanes tracked? | `docs/research_register.md` | Research lane, local files, evidence class, promote gate, and kill gate. |
| What non-heavy official accounting docs exist? | `docs/official_accounting_checklist.md` | Submission byte accounting, memory-unit risk, promoted-result receipt. |
| What offline embedding-teacher rules are allowed? | `docs/embedding_teacher_rules.md` | Distillation-only rules and forbidden model-payload shortcuts. |
| What scripts exist and what are they for? | `docs/tooling_inventory.md` | Grouped tool inventory and lock-safety expectations. |
| What cleanup/audit work remains? | `docs/organization_audit.md` | Registry drift, inventory staleness, pending memory-value rows, and doc hygiene. |
| How should the next operator continue? | `docs/takeover_runbook.md` | First checks, active candidate decision tree, promotion command pattern, update rules. |
| What receipt shape backs each claim? | `docs/evidence_receipts.md` | Standard receipts for gates, memory values, shadow residuals, and official claims. |

## Active Proof Lane

No target-bearing full-corpus proof gate is active. The unchanged CMIX21 package was
stopped after its `14,864,716`-byte `100M` first archive missed the
`14,715,573` unified-executable screen by `149,143` bytes. It must not advance
to `1G`.

Active baseline:

```text
fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1
```

Certificate-active candidate:

```text
none
```

A serialized source-wrapper replay is terminal for the exact geometry-title
`112+80` recurrent construction. Its two framed archives are byte-identical at
`1,635,671`, marker `G`, backend payload identity, roundtrip, determinism, and
clean resources all pass. The later-region matched control retains only
`4 B/1M` over native `112`, so no larger recurrent gate is authorized. The
archive-neutral individual/nested endpoint probe and its contextual selector
are complete and insufficient. No prefix can prove `109,500,000` without
counted full-corpus replay.

Retired cmix21 bracket:

```text
ppmd22400k -> ppmd22272k -> ppmd21888k -> ppmd21760k -> ppmd21632k -> ppmd21504k -> ppmd21376k -> ppmd21248k -> ppmd21120k -> ppmd20992k -> ppmd20864k -> ppmd20736k -> ppmd20608k -> ppmd20480k
```

Interpretation:

- The fx2 geometry baseline has `100M` archive `14,857,781`, counted program
  `183,008`, and calibrated full forecast `110,181,114`.
- The remaining forecast debt is `681,114` bytes.
- A global blend of original-order FX2 and the full CMIX21 final probability
  saved `1,400.007 B/1M` on sealed holdout, but that stream differs from the
  geometry `96x2` substrate and the value is not additive to its forecast.
- The original compact-family trace recorded FXCM and PAQ8 as constant midpoint
  padding outputs. `CMX21F3` corrected that observation bug while preserving
  the archive and final P1 trace exactly, but its best compact family mixture
  retained only `323.434 B/1M` on sealed holdout and is retired.
- On the exact geometry `96x2` stream, the continuously evolved full-CMIX21
  endpoint retained only `290 B/1M` overall and `355 B/1M` on internal
  opening holdout. The opening-selected blend retained only `61 B/1M` on the
  offset-`500M` same-store slice. Exact range decode passed with zero holdout
  block regressions, but the result misses the revised debt by `191.737 B/1M`
  even before integration. Existing individual and nested endpoints are
  therefore retired from selector optimization.
- The standalone PAQ-free `200x2` codec is a different construction. Its exact
  first-`1M` gain is `1,149` bytes, but its reproducible package requires
  `762.424 B/1M` and the frozen offset-`500M` slice retains only `370 B/1M`.
  Receipt: `results/fx2_cmix21_lstm200_disjoint_terminal_v1/receipt.json`.
- Native `112x2` saves `675.8 B/1M` cumulatively at `10M` but misses its
  counted archive ceiling by `1,234` bytes. Heterogeneous `112+80` improves it
  by `1,198` exact bytes and saves `795.6 B/1M`. Its accepted reproducible
  source package is `264,646` bytes. Wrapper replay passes, but the offset-`500M`
  reset slice retains only `4 B/1M` over native `112`; unchanged recurrent
  factorization is retired from larger gates.
- The static WRT dictionary boundary swap is retired: its storage proxy was
  positive, but the exact cumulative-`10M` archive regressed by `1,140` bytes.
- The WRT token-span causal specialist is retired after losing `1` exact byte
  on sealed holdout and matching its deterministic random control.
- The retired FX2-SC sidecar candidate had counted program size `256,906`; its
  canonical `10M` native-output lower bound reached `1,641,762`, which is
  `10,181` bytes above the `1,631,581` promotion ceiling before final flush.
- The compact XML residual screen failed to replace it: best cached key
  `mode_char` saved `5` held-out bytes and `-6,139` net after code.
- The block-posterior SRSTC raw receipt saves `900,464` net bytes, but the
  unchanged aggregate expert did not transfer to fx2 probabilities. The next
  SRSTC move is direct fx2 residual modeling or reversible layout, not a score
  claim from raw shadow savings.
- `ppmd20736k` reached `10,472,644` KiB during its `10M` gate, `707,019` KiB
  above official decimal `10GB`, so the PPMD-only cmix21 family is retained as
  research evidence rather than an active prize candidate.
- `ppmd20608k` passed `1,024` bytes but exceeded decimal `10GB` at `250,000`
  bytes by `240,207` KiB, so it is retained as a memory bracket.
- `ppmd20480k` passed `1,024` bytes. Its latest recorded `250,000` gate
  exceeded official decimal `10GB` by `3,275` KiB, so it is bracket evidence,
  not the active proof lane.

The promotion rule is:

```text
Do not run a larger gate until the current component has terminal archive,
roundtrip, determinism, RSS, and accounting receipts at the current scope.
```

## Primary Novel Strategy Lane

The primary research lane is:

```text
SRSTC / streaming self-referential semantic retrieval
  -> causal span parser
  -> deterministic sketch tables
  -> self-referential patch-copy probability model
  -> fixed-point regret router
  -> exact shadow receipt
  -> smallest paying integration into the strongest admissible substrate
```

This lane is allowed to use existing concepts as components: FX2-SC supplies
outer calibration, causal schema tries supply table families, embedding teachers
supply distilled sketch features, MWCC/I-SSA supply router/state coordinates,
and cmix21/fx2 supply baselines or integration backends. None of those backup
concepts becomes a target claim without its own exact receipt.

## Parallel Work Allowed While Heavy Lock Is Busy

Allowed:

- maintain docs and ledgers;
- audit official accounting;
- write residual/SSE trace specifications;
- maintain the SRSTC / streaming retrieval mixer plan and shadow receipt contract;
- design and shadow-score causal states without launching a compressor gate;
- update embedding-teacher distillation rules;
- inspect result JSONs and guard receipts;
- organize candidate contracts and source-boundary notes.

Not allowed:

- launch another compression gate;
- start a full reproduction run;
- change active candidate source under the current run;
- reinterpret prefix evidence as target proof;
- move untracked external source into a candidate without recording the source
  boundary.

## Evidence Levels

| Level | Evidence | Claim allowed |
|---:|---|---|
| 0 | Source exists | Mechanism exists. No performance claim. |
| 1 | Build/import works | Contract shape is valid. No compression claim. |
| 2 | Prefix compression only | Archive diagnostic only. |
| 3 | Prefix roundtrip | Same-scope upper bound only. |
| 4 | Prefix determinism replay | Same-scope deterministic evidence only. |
| 5 | `100M` replay under guard | Scale evidence, not full proof. |
| 6 | `1G` replay under guard | Local constructive candidate. |
| 7 | `1G` official accounting audit | Submission-grade target claim if score qualifies. |

## Candidate Folder Discipline

Every active candidate belongs under:

```text
programs/<candidate_id>/
```

Required files:

```text
program.py
meta.json
```

External binaries, dictionaries, compressed source payloads, and wrapper files
must be counted by the driver or documented as official-accounting bytes. A
candidate with untracked source files must remain in a source-tracking state
until its source boundary is reproducible.

## Report Update Rules

Use these ownership rules when adding or changing facts:

- Add measured algorithm facts to `ALGORITHMS.md`, not only chat notes.
- Add cmix21 gate posture to `CMIX21_LOCK_SAFE_QUEUE.md`.
- Add target proof state only to `UPPER_BOUND_CERTIFICATE.md` when exact result
  artifacts justify it.
- Add candidate lifecycle and registry rules to `CANDIDATES.md`.
- Add theoretical sidecar architecture to `FX2_SC.md` or `FX2_SC_PAPER.md`.
- Add official submission accounting rules to
  `docs/official_accounting_checklist.md`.
- Add residual/SSE trace schema to `docs/shadow_coder_spec.md`.
- Add cached residual/SSE measurement summaries through
  `tools/fx2_residual_shadow_matrix.py`, not hand-written tables.
- Add SRSTC / causal sketch-retrieval algorithm and proof gates through
  `tools/streaming_retrieval_mixer_plan.py`.
- Add embedding-teacher boundaries to `docs/embedding_teacher_rules.md`.

## Current Audit Findings

The tree has hundreds of candidate directories and fewer registered programs.
That is not automatically wrong: historical negative evidence and local probes
are expected. It does mean the registry, generated candidate inventory, and
active queue must be kept separate.

Known organizational risks:

- candidate directories can outpace `index.json`;
- `candidate_inventory.json` can become stale relative to the filesystem;
- result files under `results/` are generated evidence and should not become
  the only place where a strategic fact lives;
- docs can accidentally mix prefix evidence, forecasts, and exact full-corpus
  results;
- speculative algorithms can be mistaken for implemented candidates.

Mitigation:

```text
facts go into the owner doc;
measurements point to result JSONs;
proof claims stay in the certificate;
strategy gates stay in the queue;
speculation stays labeled as source-only or design-only.
```

For the current cleanup receipt, see `docs/organization_audit.md`.

For continuation after an interruption or handoff, start with
`docs/status_receipt.md`, then `docs/takeover_runbook.md`.
