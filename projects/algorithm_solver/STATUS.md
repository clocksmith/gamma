# Algorithm solver: status and handoff

Updated 2026-10-17. Everything below can be continued without Claude: the next steps use
deterministic tooling, the local model (Qwen3.5-4B), or `codex exec`.

## Goal

Build a fast algorithm-problem solver whose work comes mainly from retrieval, composition of
verified components, and verification, with little generative inference at runtime. Measure every
claim on a frozen sample with hidden-test judging, and compare against plain prompting.

## What we learned

1. Lookup works for known problems. Recognition track (`runs/baseline-v2`, 200 queries / 125 groups):
   correct decision 0.956 [0.928, 0.980], wrong match 0.024, exact 50/50, paraphrase 48/50, absent
   49/50 abstained, about 0.1 s. Weak spot: sibling problems (House Robber I/II style), 4 wrong
   matches with score margins of 0.0015-0.010.
2. For strong models, retrieval and templates add nothing. Interim paired results against
   model_alone on problems with independent tests (likely exposed to these models):
   - claude-v1 (121 problems): model_alone 0.826; retrieval 0.826 (difference 0.0 [-0.025, 0.025]);
     classify_template 0.818 (-0.008 [-0.025, 0.0]); p50 route 6 s.
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

- Held-out problems (contracts/sample_manifest.json) and their aliases never enter the index,
  retrieval, classifier training, vocabulary design, mining, or planner training.
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

## Running at handoff

- `tmux` session `algsolve-codex`: `python -m algsolve.run --run-name codex-v1 --solver codex --stages solving,report`.
  Leave it to finish; rerunning the same command resumes.
- `tmux` session `algsolve-claude` (claude-v1, about 59 items left) uses Claude. Either let it finish or stop it:
  `tmux kill-session -t algsolve-claude`. Partial results stay valid; reports rebuild from them.
- Rebuild any report: `python -m algsolve.run --run-name <run> --stages report` (no model calls).

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
