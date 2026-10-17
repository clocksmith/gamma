# Algorithm solver: status and handoff

Updated 2026-10-17. Everything below can be continued without Claude: the next steps use
deterministic tooling, the local model (Qwen3.5-4B), or `codex exec`.

## Goal

Build a fast algorithm-problem solver whose work comes mainly from retrieval, composition of
verified components, and verification, with little generative inference at runtime. Measure every
claim on a frozen sample with hidden-test judging, and compare against plain prompting.

## Two goals

- Goal 1 (minimal, primary): index the whole corpus with verified solutions and answer exact and
  similar-sounding problems by retrieval (embed, rerank, return or adapt the stored solution).
  Exact part is done: `python -m algsolve.corpus build|selftest` indexed 3,353 LeetCode problems;
  3,353/3,353 exact statements matched themselves, 2,538/2,538 returned verified solutions passed
  hidden tests, p50 0.10 s (`findings/corpus-selftest/summary.json`). Open: paraphrases and sibling
  variants over the whole corpus, a reranker for I/II/III siblings, Codeforces/AtCoder coverage.
- Goal 2 (experimental): retrieval-guided deterministic composition (embed, rerank, typed
  components, bounded search). See findings 3 and next steps 2-5.

Committed result summaries live in `findings/` (runs/ and data/ are gitignored and machine-local).

## Takeover checkpoint: retrieval interface and component mining

Work remains inside this lane. No new downloads, installs, Claude calls or paid
services were started. Existing Codex execution on `x@128.tail995236.ts.net`
continues; a complete-line snapshot now records 135/150 finished problems (121
with independent tests). See `findings/codex-v1/report.md` and `snapshot.json`.
Model-alone and retrieval both pass 0.802 on that paired independent subset;
templates pass 0.777. This is still partial, with different completed prefixes
from Claude; do not rank models or call the run complete.

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
3. Finish the still-active Codex run, rebuild its final report without changing
   raw rows, and replace the partial checkpoint. Do not restart Claude.
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
2. For strong models, retrieval and templates add nothing. Interim paired results against
   model_alone on problems with independent tests (likely exposed to these models):
   - claude-v1 (complete, 150 problems, 121 with independent tests): model_alone 0.826; retrieval
     0.826 (difference 0.0 [-0.025, 0.025]); classify_template 0.818 (-0.008 [-0.025, 0.0]); p50 route 6 s.
   - codex-v1 (109 problems): model_alone 0.817; retrieval 0.817 (0.0 [-0.028, 0.028]);
     classify_template 0.789 (-0.028 [-0.055, 0.0]); p50 route 9-10 s.
   - Retrieval wins one problem and loses one against each solver's own model_alone; templates gain
     none. The two runs cover different completed prefixes, so do not rank Claude against Codex from
     these numbers. These are paired interim results, not proof that help cannot work. Zero CLI tool
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

## Earlier handoff process descriptions (historical)

- claude-v1 finished (600/600); report in `findings/claude-v1/`.
- codex-v1 is still running on the original machine (tmux `algsolve-codex`, 125/150 problems when
  this was written). Its results exist only there; whoever has that machine should rebuild with
  `python -m algsolve.run --run-name codex-v1 --stages report`, copy `report.md`/`report.json`
  into `findings/codex-v1/`, commit and push. `findings/codex-v1/` holds the interim snapshot.

## Next steps (no Claude needed)

1. Close out the comparison.
   - When codex-v1 (and claude-v1, if left running) finish, rebuild reports and record the final
     paired table here. Expected outcome: no measurable gain from retrieval/templates for frontier CLIs.
   - Optional local control: resume the Qwen run (`--run-name baseline-v2 --solver qwen
     --stages solving,report`) to see whether help matters for a small model. Slow at 11.4 tok/s;
     speeding it up needs an approved install (flash-linear-attention + causal-conv1d) or llama.cpp.

2. Test whether a richer, mined library changes the composition picture (deterministic, index only).
   - Write `algsolve/synth/mine.py`: AST-extract helper functions, classes and inner functions from
     validated LeetCodeDataset references and Doocs `Solution.py` (index problems only), normalize
     (rename locals, strip docstrings), hash and cluster by structure, rank by frequency, keep provenance.
   - Turn the top clusters into components with written contracts and brute-force unit tests (the
     pattern in `tests/test_algorithm_solver_synth.py`); add skeletons only where a recurring control
     structure appears. This is vocabulary v2.
   - Build a fresh confirmation set from index problems not used in mining or dev (seeded, stratified).
   - Audit v2 with Codex only: `python -m algsolve.synth.audit dev --name audit-v2-confirm --proposers codex:3`
     (point `dev_problems` at the confirmation set first).
   - Decision metric: share of problems demonstrated with algorithm-specific skeletons and holes
     <= 40 nodes. If that stays near zero, retire the "choose, don't generate" premise.

3. Measure what search can actually find (A1, unguided; deterministic).
   - Write a bounded enumerator: skeleton choice x input bindings x expressions up to N nodes from a
     small operator set, checked against public examples (counterexample-guided), hidden tests only
     for final scoring.
   - Evaluate on index problems whose demonstrated compositions are small (from `runs/audit-dev-1*`
     and the v2 audit). Report solve rate, candidates explored, search time, abstentions.

4. Grammar as a fence for a generator (Codex or Qwen, no Claude).
   - New route `compose_codex`: codex proposes a composition (as in the audit), public-example
     feedback only, one repair, same budget; hidden tests only for scoring. Compare against
     codex-v1 model_alone on the frozen 150 using the paired report. Question: does constraining
     output to the grammar cost accuracy, and does it buy speed or reliability?

5. Fix the lookup weak spot with a reranker (no install).
   - Use Doppler's existing node path (`doppler/src/cli/doppler-cli.js verify` with the rerank
     workload; local models `doppler/models/local/qwen-3-reranker-0-6b-{q4k-ehf16,f16}-af32`) to
     rescore the top-10 lookup candidates. Refit thresholds on dev queries only, then rerun the
     recognition track. Target: the 4 sibling wrong matches. Note q4k scores the "yes" logit and
     f16 the yes-no difference.

6. Honest unseen-problem evaluation (needs approval for new downloads).
   - Collect problems released after the solvers' training cutoffs with official tests, then rerun
     the comparison. Until then all solving numbers are on likely-exposed problems.

## Open workspace items

- The bootstrap printed: "Preserved legacy checkout at /home/x/deco/plasma; reconcile its local
  work before creating the project link" (mutecity appears to succeed plasma).
- Root `deco` has untracked scratch directories (worktrees/, doe-native-candidate.8Ji85X/,
  doe-replay-barrier/, doe-emitters/, releases/, .local/, progress.log) left uncommitted on purpose.
