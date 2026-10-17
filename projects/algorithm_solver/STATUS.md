# Algorithm solver: status and handoff

Updated 2026-10-17. Everything below can be continued without Claude: the next steps use
deterministic tooling, the local model (Qwen3.5-4B), or `codex exec`.

## Goal

Two separate targets; neither generates source code autoregressively at runtime:

1. **Recognize known problems.** Recognize indexed problems despite rewriting and
   return their existing correct solutions. Keep the all-corpus service index
   isolated from synthesis. Measure correct/wrong matches, calibrated abstention,
   independently tested solution coverage, paraphrase/sibling/absent cases and
   complete latency. The optional Codex adaptation route is a generative baseline,
   not success on this target.
2. **Compose unfamiliar solutions.** Retrieve independently tested components and
   predict a bounded graph non-autoregressively with component, binding, parameter
   and structure heads. Assemble and validate deterministically; bounded search
   is a baseline and fallback, not the primary intended inference path.
   Mine only permitted development solutions; freeze v2 contracts and identities
   before confirmation. Audit algorithm-specific compositions with holes <=40 AST
   nodes, then compare unguided/retrieval-guided search against Codex baselines.
   Public examples reject candidates; hidden tests score final outcomes only.

Exact lookup has evidence for 3,353/3,353 indexed statements; 2,538 returned
solutions have independent passing tests. That leaves 815 indexed entries without
that evidence, not 815 demonstrated incorrect solutions. Paraphrase recognition,
sibling discrimination, absent-case coverage and practical deterministic
composition coverage remain open.

Committed result summaries live in `findings/` (runs/ and data/ are gitignored and machine-local).

## Takeover checkpoint: retrieval interface and component mining

Work remains inside this lane. No new downloads, installs, Claude calls or paid
services were started. The Codex execution on `x@128.tail995236.ts.net` has since
finished: 150/150 problems (121 with independent tests); `findings/codex-v1/report.md`
is the final report (`snapshot.json` is the earlier 135/150 snapshot). Model-alone and
retrieval both pass 0.802 on the paired independent subset; templates pass 0.777.
Do not rank Claude against Codex from these numbers.

- `algsolve/answer.py`: a JSON CLI and injected Python interface for a future
  editor mode. Retrieve, optionally rerank with separate calibrated thresholds,
  verify against **query** public examples, then optionally adapt through the
  existing Codex generation/repair path. No examples or missing sandbox means
  abstention. A failed generated candidate is never returned as approved code.
  Source attribution survives; original-reference validation is distinct from
  query correctness. The real Two Sum smoke passed its public examples through
  the Linux sandbox; independent query tests were not evaluated. Receipt:
  `findings/editor-answer-smoke-20261017/`.
- `algsolve/corpus_recognition.py`: all 150 existing known-query recognition
  cases against 3,353 corpus entries, CPU float32 embeddings, original thresholds,
  no refitting. Exact 50/50, paraphrase 48/50 (2 abstentions), siblings 43/50
  (4 wrong matches, 3 abstentions). Existing model-generated paraphrases retain
  original starter signatures; these are not human paraphrases or unseen tasks.
  Old absent queries are excluded because full-corpus membership changed.
  Receipt: `findings/corpus-recognition-20261017/`.
- `algsolve/rerank.py`: local-only Doppler adapter, tested with the existing
  Qwen3-Reranker-0.6B F16 artifact on Node/WebGPU. The synthetic sum/max pair
  scores 4.888988/0.161398 respectively; five built-in semantic checks pass.
  The adapter restores candidate order and rejects incomplete, non-finite,
  duplicate or input-mismatched scores. This is connectivity evidence only;
  no algorithm-sibling calibration or reranker improvement claim. Receipt:
  `findings/reranker-probe-20261017/`.
- `algsolve/synth/mine.py`: deterministic index-only AST mining, preserving
  source hashes, licenses and attribution. Reserved 66 problems in 60 fresh
  sibling families, stratified by difficulty, before inspecting solution ASTs.
  Of 3,207 remaining entries, 2,446 have validated references used in mining:
  5,679 clusters, 79 recurring across problems, 44 across distinct families,
  zero parse failures. Top repeats are largely union-find/Fenwick operations
  already present in v1. Structural hashes are not semantic equivalence or
  newly verified components. V1 remains unchanged (`2cdc0dbf…`). Receipts:
  `findings/mine-v2-candidates-20261017/` (split and summary); complete candidate
  source/provenance remains in the matching remote `runs/` directory.

### Next bounded decisions

1. Fit the reranker's acceptance threshold and margin on the existing 60
   development queries only; bind the model manifest and scoring semantics to
   that calibration. Then evaluate the frozen recognition queries once, comparing
   wrong matches, correct matches, abstentions and total latency. Do not tune on
   the four observed test-set sibling failures.
2. Inspect cross-family mining candidates that add capabilities beyond v1.
   Write explicit contracts and brute-force tests before freezing a separate v2;
   audit on the reserved confirmation families with Codex only. The production
   target remains generation-free composition, measured by algorithm-specific
   compositions with holes <=40 nodes, not merely expressibility.
3. Codex comparison closure is complete. Preserve the final reports and raw rows;
   do not rerun Codex or restart Claude merely to close the handoff.
4. Follow `editor-protocol.md` before connecting an editor. No browser mode is
   deployed: the current corpus/judge emits Python, not JavaScript; the static
   lab cannot run the Linux sandbox. This lane prepares a research interface,
   not an unauthenticated code-execution service. User input encodings and
   problem-solving modes remain separate; insertion must be explicit.

Acceptance evidence: the existing judge/lane/synthesis tests pass (45 tests).
New answer/mining tests plus the existing lane tests pass (20); the subsequent
family-count checks pass (3) and reranker adapter checks pass (2). The real
answer CLI and Doppler adapter were exercised on `128`. Test generators are
fixtures; they do not establish Codex adaptation quality. All executions log
`[run-contract]`. See the takeover receipt for exact commands.

Component: algorithm_solver. Intent: deliberately extended to the user-authorized
retrieval interface and index-only mining; frozen comparisons preserved. Boundary
effects: none outside Gamma; no production website changes.

## What we learned

1. Lookup works for known problems. Recognition track (`runs/baseline-v2`, 200 queries / 125 groups):
   correct decision 0.956 [0.928, 0.980], wrong match 0.024, exact 50/50, paraphrase 48/50, absent
   49/50 abstained, about 0.1 s. Weak spot: sibling problems (House Robber I/II style), 4 wrong
   matches with score margins of 0.0015-0.010.
2. Retrieval and templates did not improve either tested frontier solver. Final paired results against
   model_alone on problems with independent tests (likely exposed to these models):
   - claude-v1 (complete, 150 problems, 121 with independent tests): model_alone 0.826; retrieval
     0.826 (difference 0.0 [-0.025, 0.025]); classify_template 0.818 (-0.008 [-0.025, 0.0]); p50 route 6 s.
   - codex-v1 (complete, 150 problems, 121 with independent tests): model_alone 0.802; retrieval
     0.802 (0.0 [-0.033, 0.033]); classify_template 0.777 (-0.025 [-0.058, 0.008]); p50 route 11 s.
   - Retrieval wins and loses equally against each solver's own model_alone (Claude 1/1, Codex 2/2);
     templates win 0-1 and lose 1 (Claude) or 4 (Codex). Do not rank Claude against Codex from these
     numbers (different solvers, same frozen sample). These are paired results on likely-exposed
     problems, not proof that help cannot work. Zero CLI tool
     items recorded.
3. Composition from the frozen vocabulary does not replace generation. Held-out audit stopped
   early by decision (`runs/audit-heldout-1/STOPPED.json`, 44 LeetCode-style problems): 41
   demonstrated expressible, but 35 only through generic skeletons (new logic written into a
   loop/formula hole); 6 algorithm-specific; 0 algorithm-specific with small holes (<= 40 AST
   nodes); median hole size 58 nodes. A chooser that only picks skeletons and bindings would cover
   close to none of these problems. Index dev audit (60 problems) showed the same pattern.
4. Local Qwen3.5-4B runs at 11.4 tok/s on transformers (torch fallback for linear attention);
   it was stopped after 89 solving records by user decision.

## Ground rules to keep

- Held-out problems (contracts/sample_manifest.json) and aliases never enter the research index,
  retrieval, classifier training, vocabulary design, mining, or planner training. The separately
  named all-corpus service index is only for known-problem retrieval, never held-out solving.
- Expected outputs never enter the sandbox; verdicts fail closed. Report `example_passed` and
  `independent_tests_passed` separately; `benchmark_judge_accepted` is not evaluated.
- The vocabulary in contracts/synth_vocabulary.json (sha256 2cdc0dbf...) is frozen. Any expanded
  vocabulary is v2 and needs a fresh confirmation set that was not used to build it.
- Label results: held out from our pipeline; prior model exposure unknown (likely for frontier
  models). Initial comparisons, not rankings.
- Gamma workflow: commit on main, push (`rdpush gamma`), log `[run-contract]` for runs.

## Where things are (paths relative to gamma/projects/algorithm_solver)

| Path | What |
|---|---|
| `algsolve/judge/` | bubblewrap sandbox, in-sandbox harness, host-side verdicts |
| `algsolve/importers.py`, `values.py`, `validate.py` | problem records, AST-parsed tests, reference validation |
| `algsolve/splits.py`, `prepare.py` | index (3,273 LeetCode problems), aliases, near-duplicates, frozen sample |
| `algsolve/lookup.py`, `embed.py`, `classify.py`, `patterns/catalog.py` | lookup, embeddings, TF-IDF classifier, 13 templates |
| `algsolve/routes.py`, `model.py`, `cli_solvers.py`, `run.py`, `report.py` | four routes; qwen / claude / codex solvers; runner; report |
| `algsolve/synth/` | grammar, 17 components, 21 skeletons, AST renderer, expressibility audit |
| `contracts/` | run contract, frozen sample, lookup thresholds, classifier metrics, frozen vocabulary |
| `data/` (gitignored) | sources + hash manifest, derived records, hidden tests, embeddings, paraphrases |
| `runs/` (gitignored) | `baseline-v2` (recognition + stopped Qwen), `claude-v1`, `codex-v1`, `audit-dev-1*`, `audit-heldout-1` |
| `../../tests/test_algorithm_solver_{judge,lane,synth}.py` | 23 judge, 11 lane, 12 synthesis tests |

Python: `/home/x/deco/gamma/.venv_rocm/bin/python`, run from this directory (the plain `.venv` lacks NumPy).

## Setting up on another machine

`data/` and `runs/` are not in git. To regenerate (Linux with bubblewrap and prlimit is required;
the judge fails closed without them):

1. Python env with torch, transformers >= 5.2, peft, datasets, pyarrow, numpy, scikit-learn 1.9.1,
   huggingface_hub.
2. `python -m algsolve.fetch` (approved sources, about 9.7 GB including Qwen3.5-4B; `--only datasets
   --only doocs` skips the model, which only the qwen solver needs).
3. Embedding model: download `Qwen/Qwen3-Embedding-0.6B` and set `ALGSOLVE_EMBEDDING_DIR` to it;
   `embed.py` verifies model.safetensors sha256 0437e45c... Use `ALGSOLVE_DEVICE=cpu` without a GPU.
4. `python -m algsolve.prepare inspect`, then `prepare freeze` (rebuilds the index; it refuses to
   redraw the committed manifest and exits after writing the index), then `prepare decode`.
5. Goal 1: `python -m algsolve.corpus build` then `python -m algsolve.corpus selftest`.
6. `claude -p` / `codex exec` solvers need those CLIs logged in; the qwen solver needs a GPU.

## Current takeover and next execution

The owning session has taken over at the user's request. Workspace `rdpull`
completed; local and `128` Gamma checkouts were clean at `d8b8711b1`. Process
inspection on both hosts found no active algorithm-solver run. The final Codex
report covers 150/150 problems and all four routes; 121 have independent tests.
`findings/codex-v1/snapshot.json` and the earlier takeover receipt are historical
partial observations, not the final report. No raw comparison rows were changed.

1. **Restore real reranker execution, then calibrate recognition.** The first
   development query (`dq000`, number-of-different-subsequences-gcds, top 10)
   reproduced Vulkan device loss twice on `128`. Model loading completed;
   prefill selected `prefill_streaming_f16kv`; RADV reported a guilty hard
   recovery and `VK_ERROR_DEVICE_LOST`, followed by the secondary cleanup error
   “BufferPool requires a live GPU device.” No query scores, calibration or
   evaluation results were produced. See
   `findings/reranker-algorithm-probe-20261017/receipt.json`. The next execution
   task is to qualify this same untruncated query/candidate workload through
   Doppler before expanding the run. Do not hide this failure as an abstention
   or shorten away constraints to make the probe pass.

   **Calibration path ready, runtime qualification open.**
   `algsolve/rerank_recognition.py` adds resumable `dev` and `evaluate` stages.
   Fit only the existing 60 development queries; freeze thresholds before the
   200 evaluation queries. Binding includes corpus, query text, active index,
   model manifest, Doppler revision and scoring source. Incomplete development
   cannot produce calibration. Original absent questions now occur in the corpus,
   so this diagnostic excludes their canonical sibling family per query. Report
   these controlled absent cases separately; natural full-corpus absent coverage
   still needs an independently specified set. Report cold-per-query Doppler
   process/model-loading cost separately from retrieval, with combined p50/p95.

   From this directory on `128` (use a new run name after source/runtime changes; append `--limit 2` for a bounded probe):
   ```sh
   /home/x/deco/gamma/.venv_rocm/bin/python -m algsolve.rerank_recognition dev --name corpus-rerank-v1 --cli /home/x/deco/doppler/src/cli/doppler-cli.js --model-dir /home/x/deco/doppler/models/local/qwen-3-reranker-0-6b-f16-af32
   ```
   Use the same arguments with `evaluate` only after calibration exists. The
   current adapter starts a fresh Node runtime per query; do not describe these
   latencies as steady-state serving. Evaluation reports recognition decisions
   and stored validation provenance, not newly judged correct answers.

2. **Build verified v2 components from existing mining output.** Mining and the
   fresh 66-problem/60-family reservation already exist; do not redraw the split
   or repeat mining as unfinished work. Inspect cross-family candidates beyond
   v1, write explicit contracts and independent brute-force tests, then freeze v2.
   An offline Codex expressibility audit is distinct from runtime generation-free
   solving. Keep the <=40 AST-node metric, but do not equate expressibility with
   a deterministic solver finding the solution.

3. **Learn direct graph prediction from verified targets.** The chosen architecture
   is a retrieval-conditioned encoder with interacting program slots, parallel
   component/EMPTY, binding, parameter and structure predictions, and optionally
   bounded refinement. Deterministic compilation and execution remain authoritative.
   `algsolve/synth/graph_targets.py` implements the initial bounded target format
   and compiler; `training_pairs.py` requalifies permitted development audit
   proposals against public and independent tests. V1 is unchanged. Current
   target support is functional IO, three stage slots, algorithm-specific
   structure and <=40 total hole AST nodes. Hole logic is retained as structured
   ASTs, not hidden behind a component ID. This is data/compiler scaffolding:
   no neural predictor, learned weights or fast-solving result exists yet.

   Split connected groups of problem identities and structural patterns together
   so alternative graphs cannot leak across training and pattern confirmation.
   Keep the separately reserved confirmation families entirely out of this
   dataset. First measure independently judged first-prediction correctness,
   wrong acceptance, coverage, warm/cold complete latency and memory. Report
   refinement rounds and retry results separately. Build bounded unguided and
   retrieval-guided search as matched baselines/fallbacks, retaining explored
   candidates. Existing Codex results remain the autoregressive baseline.

   The real `graph-targets-v1` export completed on `128`: 65 input audit rows,
   3 duplicate proposals, 1 independently requalified training pair (`lcd:323`),
   48 rejected by the algorithm-specific/<=40-node gate, 7 without independent
   or public tests, 2 outside permitted development, and 4 without demonstrated
   compositions. No pattern-confirmation pair exists in this one-pair export.
   All 54 focused judge/lane/synthesis/graph-target tests passed. Receipts:
   `findings/graph-targets-v1/`; complete pair data stays in the ignored remote
   `runs/graph-targets-v1/`. No model calls or training occurred. The next asset
   is a larger, independently tested v2 development graph corpus; neither neural
   predictor accuracy nor fast unfamiliar-problem solving is established.

   This composition-data work can proceed independently of the Doppler device-loss
   blocker. Preserve the one-pair result and grow verified v2 coverage before any
   training campaign.

New problem downloads and model installations require separate authorization.
The Qwen run remains stopped. The existing answer interface defaults to no
fallback and checks query examples with provenance; editor deployment is not
part of this takeover.

## Open workspace items

- The bootstrap printed: "Preserved legacy checkout at /home/x/deco/plasma; reconcile its local
  work before creating the project link" (mutecity appears to succeed plasma).
- Root `deco` has untracked scratch directories (worktrees/, doe-native-candidate.8Ji85X/,
  doe-replay-barrier/, doe-emitters/, releases/, .local/, progress.log) left uncommitted on purpose.
