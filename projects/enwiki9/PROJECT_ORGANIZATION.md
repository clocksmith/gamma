# enwiki9 Project Organization

This file is the ownership map for the `enwiki9` compression project. It
defines where strategy, algorithms, evidence, tools, and submission accounting
belong so the project does not drift back into scattered notes.

## Current Operating Thesis

The project has one proof objective:

```text
full enwik9 official score <= 109,500,000 bytes
```

The project currently has no full-corpus constructive proof at that target.
The active native proof lane is
`cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`.
It passed exact `1K`, `250K`, and `1M` gates and is running unchanged at `10M`.
The primary novel residual strategy is SRSTC / streaming self-referential
semantic retrieval: a causal probability model built from already-decoded
spans, deterministic sketches, self-referential tables, patch-copy priors, and
fixed-point regret routing.

The older structural concepts are not discarded. They become backup lanes,
baselines, SRSTC components, or offline-teacher discovery tools until exact
receipts show that one should be promoted.

## Source Of Truth Map

| Question | Source of truth | What belongs there |
|---|---|---|
| What is the project and how are results reported? | `README.md` | Scoring math, result JSON fields, scope discipline, reporting vocabulary. |
| What algorithms exist and what evidence do they have? | `ALGORITHMS.md` | Mechanism explanations, measured rows, current strategy register, paper/design note index. |
| How can a reader orient on the main algorithms? | `docs/algorithm_cards.md` | Plain-English cards: mechanism, score, proof boundary, next role. |
| What artifact-backed rows currently rank best by scope? | `docs/evidence_matrix.md` | Generated score/archive matrix from result JSONs only; no forecasts or inherited metadata. |
| What are the top rows without the full evidence matrix? | `docs/best_results.md` | Generated compact top-three score/archive rows for selected measured scopes. |
| What is the current one-page operator status? | `docs/status_receipt.md` and `docs/status_receipt.json` | Generated target state, lock state, active RSS, gate decision, and proof boundary. |
| What candidate folders are valid or retired? | `CANDIDATES.md` | Candidate contract, lifecycle, evidence basis, retirement rules, audit commands. |
| What is the generated candidate audit snapshot? | `CANDIDATE_INVENTORY.md` and `candidate_inventory.json` | Generated inventory and status counts. Do not hand-edit generated facts. |
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
| What evidence level does a teacher, shadow, prefix, block, or full replay prove? | `ALGORITHMS.md` and `docs/research_register.md` | Five-level evidence ladder separating proxy forecasts, target-substrate shadows, counted prefix receipts, disjoint block receipts, and full official score claims. |
| Where are strategy and novel-algorithm research lanes tracked? | `docs/research_register.md` | Research lane, local files, evidence class, promote gate, and kill gate. |
| What non-heavy official accounting docs exist? | `docs/official_accounting_checklist.md` | Submission byte accounting, memory-unit risk, promoted-result receipt. |
| What offline embedding-teacher rules are allowed? | `docs/embedding_teacher_rules.md` | Distillation-only rules and forbidden model-payload shortcuts. |
| What scripts exist and what are they for? | `docs/tooling_inventory.md` | Grouped tool inventory and lock-safety expectations. |
| What cleanup/audit work remains? | `docs/organization_audit.md` | Registry drift, inventory staleness, pending memory-value rows, and doc hygiene. |
| How should the next operator continue? | `docs/takeover_runbook.md` | First checks, active candidate decision tree, promotion command pattern, update rules. |
| What receipt shape backs each claim? | `docs/evidence_receipts.md` | Standard receipts for gates, memory values, shadow residuals, and official claims. |

## Active Proof Lane

The active target-bearing proof gate is:

```text
cmix21 public 108,244,767-byte external anchor
  -> global FXCM cmC2/2 memory cut plus original rolling buffer
  -> exact 250K archive-neutral pass
  -> exact 1M archive 174525, roundtrip and determinism pass
  -> unchanged 10M gate
```

Active baseline:

```text
fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1
```

Certificate-active candidate:

```text
cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1
```

This package is target-bearing only as a constructive promotion lane; no prefix
result is a `109,500,000` proof.

Retired cmix21 bracket:

```text
ppmd22400k -> ppmd22272k -> ppmd21888k -> ppmd21760k -> ppmd21632k -> ppmd21504k -> ppmd21376k -> ppmd21248k -> ppmd21120k -> ppmd20992k -> ppmd20864k -> ppmd20736k -> ppmd20608k -> ppmd20480k
```

Interpretation:

- The fx2 geometry baseline has `100M` archive `14,857,781`, counted program
  `183,008`, and calibrated full forecast `110,181,114`.
- The remaining forecast debt is `681,114` bytes.
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
  not the active proof lane, even though the generated certificate still names
  the same full candidate id as the operator active gate.

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
