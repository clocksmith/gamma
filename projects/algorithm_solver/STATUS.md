# Algorithm solver: status and handoff

Updated 2026-10-17. Interim numbers below are labelled as such; final numbers come from
`runs/<run>/report.md` and `runs/<audit>/summary.json`, rebuilt from results files.

## Goals

1. Measure whether help (known-answer lookup, retrieved solved examples, an algorithm-pattern
   classifier with templates) makes a solver faster or more reliable than the same solver alone,
   on a frozen sample with hidden-test judging.
2. Synthesis track (user-approved stages 1-2): test whether solutions can be built from a frozen,
   typed vocabulary of tested components and skeletons instead of free-form code. First number:
   demonstrated coverage of the 150 held-out problems.
3. Later (not started): retrieval-guided and learned composition planners (A1-B3 grid), novel
   composition holdout, reranking, live paste/edit interface.

## Ground rules (from the approved plan)

- Held-out problems and their aliases/near-duplicates never enter the index, retrieval, classifier
  training or vocabulary design. Recognition (lookup) and solving are separate tracks.
- Expected outputs never enter the sandbox; verdicts fail closed. Evidence levels stay separate:
  `example_passed`, `independent_tests_passed`, `benchmark_judge_accepted` (not evaluated).
- Dataset label: held out from our pipeline; prior model exposure unknown (likely exposed for
  Claude/Codex). Compare routes, not absolute rates. Initial comparison, not a ranking.
- The synthesis vocabulary was built from index problems only, frozen (hash below), and is not
  changed after the held-out audit; an expanded vocabulary needs a fresh confirmation set.

## Where things are

| Path | What |
|---|---|
| `algsolve/judge/` | bubblewrap sandbox, in-sandbox harness, host-side verdicts (stdin + functional) |
| `algsolve/importers.py`, `values.py`, `validate.py` | records from LeetCodeDataset, Doocs, LiveCodeBench v6 file, Codeforces; AST-parsed tests; reference validation |
| `algsolve/splits.py`, `prepare.py` | index, aliases, near-duplicates, frozen sample |
| `algsolve/lookup.py`, `embed.py`, `classify.py`, `patterns/catalog.py` | lookup (Qwen3-Embedding-0.6B + fingerprint rescoring), TF-IDF classifier, 13 templates |
| `algsolve/routes.py`, `model.py`, `cli_solvers.py`, `run.py`, `report.py` | four routes; Qwen3.5-4B, `claude -p`, `codex exec` solvers; runner; report |
| `algsolve/synth/` | grammar, 17 components, 21 skeletons, AST renderer, expressibility audit |
| `contracts/run_contract.json`, `sample_manifest.json` | budgets, solvers, frozen sample (sha256 `40da673a...`) |
| `contracts/lookup_thresholds.json`, `classifier_metrics.json` | fitted on dev/index data only |
| `contracts/synth_vocabulary.json` | frozen vocabulary (sha256 `2cdc0dbf...`), dev-audit history |
| `data/` (gitignored) | fetched sources with hash manifest, derived records, tests, embeddings, paraphrases |
| `runs/` (gitignored) | per-run results, logs, reports |
| `../../tests/test_algorithm_solver_*.py` | judge (fail-closed), lane, synthesis contract tests |

## Done

- Data: approved downloads (9,726,341,702 bytes) hash-recorded in `data/raw/fetch_manifest.json`.
  Qwen3.5-4B in the HF cache; Qwen3-Embedding-0.6B read in place from Doppler's verified copy.
- Judge: 23 fail-closed tests; mutation checks show the network and host-file tests fail on a leaky sandbox.
- Recognition track (`runs/baseline-v2`, complete): 200 queries / 125 groups. Correct decision
  0.956 [0.928, 0.980]; wrong-match 0.024; exact 50/50, paraphrase 48/50 (2 abstain), sibling
  families 0.86 correct with 4 wrong matches (margins 0.0015-0.010; dev-fitted margin is 0),
  absent 49/50 abstained. 144/146 returned solutions pass the true problem's hidden tests.
  Lookup p50 0.096 s.
- Qwen3.5-4B solving: stopped by user decision at 89 records (`runs/baseline-v2/STOPPED.json`).
  Measured 11.4 tok/s (transformers torch fallback for linear attention).
- `runs/baseline-v1`: aborted for a fingerprint bug (`ABORTED.json`).
- Synthesis stage 1: vocabulary built and frozen. Dev audit on 60 index problems: 58 demonstrated
  expressible after fixes (38 of the first 56 used only generic skeletons), 2 unresolved.

## Running (tmux sessions; results resume on rerun)

| Session | Command | Log / results |
|---|---|---|
| `algsolve-claude` | `python -m algsolve.run --run-name claude-v1 --solver claude --stages solving,report` | `runs/claude-v1/` |
| `algsolve-codex` | same with `codex-v1 --solver codex` | `runs/codex-v1/` |
| `algsolve-audit-heldout` | `python -m algsolve.synth.audit heldout --name audit-heldout-1` | `runs/audit-heldout-1/` |

Interim snapshot, 2026-10-17, rebuilt from the live runs on `x@128`
(using `/home/x/deco/gamma/.venv_rocm/bin/python`; the plain `.venv` lacks NumPy):

| Run | Complete problems / independent-test problems | Alone / retrieval / templates | Median route seconds |
|---|---|---|---|
| claude-v1 | 129 / 121 | 82.64% / 82.64% / 81.82% | 6.16 / 6.58 / 6.11 |
| codex-v1 | 96 / 96 | 81.25% / 81.25% / 78.12% | 9.55 / 10.11 / 10.22 |

Each retrieval route wins one problem and loses one against its own model-alone
baseline. Templates gain none and lose one (Claude) or three (Codex). These are
paired interim results, not proof that help cannot work. The runs cover different
completed prefixes and must not be used to rank the solvers. Lookup answers no
held-out problem by design. The report records zero CLI tool items.

The held-out vocabulary audit snapshot covers 36/150 problems, all from LCD:
34 demonstrated expressible against independent tests, two unresolved. Of the
34 successes, 28 use generic skeletons only. Rendered hole-node counts range
from 12 to 199. This is partial demonstrated coverage, not a final coverage rate
or evidence of successful specialized-component reuse.

All three runner processes were observed alive and their append-only result
counts increased during inspection. Reporting only was invoked; no new solver,
training, planner, reranker or download was launched. The frozen vocabulary and
sample remain unchanged. Rebuild after completion before drawing conclusions.

If a run stops with `[solver-unavailable]` (subscription limit), rerun the same command; finished
items are skipped. Rebuild a report any time: `python -m algsolve.run --run-name <run> --stages report`.

## Next

1. When the CLI runs finish: report paired pass rates per route vs model_alone, first attempt vs
   repair, latency, failure types, by source and date; label all as likely exposed.
2. When the held-out audit finishes: report demonstrated coverage by source, skeleton family
   (generic vs algorithm-specific), hole-node size, outside-grammar categories, unresolved.
3. Then, with user approval: unguided/retrieval-guided/learned synthesis configurations (A1-B3),
   structured requirement specs for the 150 (hand-written, no algorithm hints), novel-composition
   holdout, reranking via Doppler's existing node path (`doppler-cli.js verify` rerank workload,
   local q4k/f16 Qwen3-Reranker artifacts; no install needed).

## Open items for the user

- reploid has uncommitted changes deleting most of `self/cloud-access-windows.js` and
  `self/cloud-access-status.js` (5,846 lines). Not from this work; `rdpush` was run for gamma only
  so they were not auto-committed.
- `mutecity` is listed in `ouroboros/deco/tools/workspace-repos.json` but absent locally, which
  makes repo-less `rdstatus`/`rdpull`/`rdpush` fail with `spawnSync git ENOENT`.
- Old `deco-sync` stashes remain in reploid (dated 2026-10-12 and 2026-10-13).
