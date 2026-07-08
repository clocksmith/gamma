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
The active proof lane is still `cmix21` memory-shaped text mode because it owns
the serialized exact gate. The primary novel strategy is now SRSTC / streaming
self-referential semantic retrieval: a causal probability model built from
already-decoded spans, deterministic sketches, self-referential tables,
patch-copy priors, and fixed-point regret routing.

The older structural concepts are not discarded. They become backup lanes,
baselines, or SRSTC components until exact receipts show that one should be
promoted.

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
| Where are strategy and novel-algorithm research lanes tracked? | `docs/research_register.md` | Research lane, local files, evidence class, promote gate, and kill gate. |
| What non-heavy official accounting docs exist? | `docs/official_accounting_checklist.md` | Submission byte accounting, memory-unit risk, promoted-result receipt. |
| What offline embedding-teacher rules are allowed? | `docs/embedding_teacher_rules.md` | Distillation-only rules and forbidden model-payload shortcuts. |
| What scripts exist and what are they for? | `docs/tooling_inventory.md` | Grouped tool inventory and lock-safety expectations. |
| What cleanup/audit work remains? | `docs/organization_audit.md` | Registry drift, inventory staleness, pending memory-value rows, and doc hygiene. |
| How should the next operator continue? | `docs/takeover_runbook.md` | First checks, active candidate decision tree, promotion command pattern, update rules. |
| What receipt shape backs each claim? | `docs/evidence_receipts.md` | Standard receipts for gates, memory values, shadow residuals, and official claims. |

## Active Proof Lane

The active proof lane is:

```text
cmix21 memory-shaped candidate
  -> exact 1M replay
  -> exact 10M replay
  -> exact 100M replay
  -> exact 1G replay
  -> official accounting audit
```

Current working family:

```text
ppmd22400k -> ppmd22272k -> ppmd21888k -> ppmd21760k -> ppmd21632k -> ppmd21504k -> ppmd21376k -> ppmd21248k -> ppmd21120k
```

Active candidate ID:

```text
cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1
```

Interpretation:

- `ppmd22400k` is the high-quality archive reference.
- `ppmd22272k` is the upper memory bracket after passing exact `10M` but
  failing the unchanged `100M` memory gate.
- `ppmd21888k` passed exact `10M` replay but failed the unchanged `100M` RSS
  guard by `36` KiB before a scored archive or roundtrip.
- `ppmd21760k` passed exact `10M` replay but failed the unchanged `100M` RSS
  guard by `72` KiB before a scored archive or roundtrip.
- `ppmd21632k` passed exact `10M` replay but failed the unchanged `100M` RSS
  guard by `68` KiB before a scored archive or roundtrip.
- `ppmd21504k` passed exact `10M` replay but failed unchanged `100M` RSS by
  `72` KiB before a scored archive or roundtrip.
- `ppmd21376k` passed exact prefix replays but failed unchanged `100M` RSS by
  `116` KiB before a scored archive or roundtrip.
- `ppmd21248k` is the active restarted ladder; its exact `1,024`,
  `250,000`, and `1,000,000` byte replays passed and the active gate is
  unchanged `10,000,000` bytes.

The promotion rule is strict:

```text
Do not retune between gates unless the candidate fails the current gate.
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
- Add active cmix21 gate posture to `CMIX21_LOCK_SAFE_QUEUE.md`.
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
