# Algorithm solver: status and handoff

Updated 2026-10-17. Component: `algorithm_solver`. Intent preserved: fast known
recognition and separately learned, generation-free composition. **The overall
composition goal is not finished.** The current known-answer route has measured
end-to-end evidence; the first composition student has no generalization win.

## Two goals

1. Recognize indexed problems despite rewriting and return an existing correct
   solution without generating code. Distinguish siblings, abstain on uncertain
   matches, preserve provenance, and verify the query's public examples.
2. Predict reusable algorithms, bindings and parameters in parallel, assemble
   an executable graph deterministically, and solve unfamiliar combinations
   quickly. Count retrieval, prediction, assembly and checking. Search is a
   baseline/fallback; autoregressive code generation is not this runtime target.

The all-corpus service index is for goal 1 only. Never use it to train or evaluate
unfamiliar composition. Raw datasets, model checkpoints and per-query rows remain
in ignored `data/` and `runs/` on `x@128.tail995236.ts.net`.

## Current known-answer qualification

`findings/corpus-answer-gpu-v2/` records the actual answer route on all 200 frozen
recognition queries, with no reranker, generation, repairs or threshold changes.
Hardware: Radeon 8060S, ROCm 7.2 / PyTorch 2.12.1; local Qwen3-Embedding-0.6B,
float16. Stored solutions execute in the existing Linux sandbox.

| Query kind | Returned / queries | Passed independent tests | Wrong accepted in these tests | Median answered latency |
|---|---:|---:|---:|---:|
| Exact | 50/50 | 50 | 0 | 154 ms |
| Paraphrase | 48/50 | 48 | 0 | 179 ms |
| Sibling paraphrase | 46/50 | 46 | 0 | 163 ms |
| Controlled absent | 0/50 | — | 0 | All abstained |

This is **144 independently tested answers out of 150 known queries**, plus
50/50 controlled abstentions. Warm answered p95 is 227–296 ms by known-query kind.
Embedding load is separately 3.00 seconds; independent scoring is outside response
latency. These numbers do not establish natural absent-problem recognition, human
paraphrase comprehension, unseen solving, or universal correctness.

Four sibling retrieval misidentifications remain. Three returned alternative
stored solutions passed the available independent tests; that does not establish
correct problem identity. Two controlled-absent retrieval matches were rejected
by the public-example gate. Paraphrases retain original signatures and use the
original public examples.

The first run returned only 117 answers because 29 known-query cases lacked
parsed examples. `values.py` now recognizes JSON `true`, `false`, and `null` as
AST literals; `importers.py` handles escaped carriage-return suffixes and preserves
whitespace inside quoted strings. `public_examples.py` recovers complete explicit
examples from the statement without hidden tests or model calls. Partial parsing
still fails closed. Original imported files and the first run remain unchanged.

The matched 60-query GPU development check preserved every CPU decision and
measured recognition-only p50/p95 of 96/192 ms. See
`findings/corpus-embedding-gpu-dev-v1/`. The corpus still has 3,353 entries and
2,538 stored solutions with prior independent validation; the remaining 815 are
an evidence gap, not demonstrated incorrect solutions.

### Use the answer interface

On host 128, from `projects/algorithm_solver`:

```sh
../../.venv_rocm/bin/python -m algsolve.answer query.json --index corpus --device cuda
```

The default is CPU and no generation. The Python API can retain the embedding
model across calls. The CLI pays cold startup per process. Explicit statement
examples may be parsed when `public_tests` is empty. See `editor-protocol.md`.
No editor/browser service or automatic insertion has been deployed.

### Reranker: repaired execution, rejected configuration

The long-query failure was traced to the manifest-selected serial streaming
prefill path. An explicit existing Doppler head128 execution patch completed the
same untruncated query and ten candidates. A second adapter bug rejected valid
scores because Doppler trims outer whitespace; Gamma now canonicalizes before
sending and retains exact response binding. No Doppler runtime or weights changed.
The default streaming path's failures remain in the earlier receipts.

The full 60-query development fit completed. At zero wrong matches, reranking
accepted **30/50 known queries**, versus **49/50** for embedding retrieval; total
p50 was **13.03 s** versus **1.23 s** on CPU embedding. This configuration was
rejected before the 200-query reranker evaluation. Do not tune it on evaluation
failures or enable it by default. Receipts: `findings/corpus-rerank-head128-v1/`
and `findings/reranker-head128-20261017/`.

The optional answer CLI can load its exact frozen calibration with `--rerank-run`,
`--doppler-cli`, and `--reranker-model` (CPU/corpus only). It verifies development
rows, refits thresholds for identity checking, and rejects changed inputs, model,
execution config or Doppler revision. This is a reproducibility interface, not
promotion of the rejected reranker.

## Composition: implemented and tested, not qualified

V1 remains unchanged at `2cdc0dbf…`. Its earlier export still has one valid pair
from 65 audit rows; preserve `findings/graph-targets-v1/` and the poor v1 audit
coverage. Those results did not establish a ceiling on better decompositions.

`call_graph.py` adds a separate candidate v2 representation: up to three explicit
algorithm-call nodes, checked references, no dead algorithm nodes, and at most
40 total glue AST nodes. It exposes existing v1 library algorithms directly.
Only fixed-width window sums is a new algorithm; it passed randomized slice-sum
oracle tests and independent tests on three distinct development problems.

Of 23 manually composed, selected development proposals, **22 qualify** after
fresh public and independent judging. One remains above the size bound. This is
a training-data asset, not a random-sample coverage estimate. Research-index
policy excludes solving, recognition and reserved confirmation sibling families.
Connected identities, sibling families and structural patterns remain together.
Receipts: `findings/call-graph-dev-v2-requalified/`; the earlier 19-pair run remains
in `findings/call-graph-dev-v2/`.

Two test defects were fixed rather than fitting code to their outputs:

- Course Schedule II now accepts any valid topological ordering, with cycle,
  permutation and edge checks on the host. Candidate execution never sees answers.
- Two imported vowel-range cases exceeded the declared array bounds. A versioned,
  case-hash-bound overlay corrects the two endpoints, preserves all cases and
  expected outputs, and checks them against a direct-count oracle. Raw files and
  historical results remain unchanged; changed source cases fail closed.

### Parallel predictor pilot

`parallel_graph.py` implements a two-layer slot transformer with parallel
component/EMPTY, expression-template and input/prior-output binding heads.
Retrieval supplies four component contracts. The 149,505-parameter graph head
uses the frozen 0.6B embedding model; it is not the whole pipeline's model size.
No source tokens, autoregressive loop, search or retries occur at inference.

The frozen 17-training/5-development-pattern split trained for 200 CPU steps:
17/17 training programs passed independent tests, **0/5 confirmation programs**
did. The nearest-training-graph baseline also scored 0/5. Four confirmation
targets need expression templates absent from training; three use operators
without training examples. **None has complete training support.** This pilot
proves fitting/assembly and exposes data/codec gaps, not learned composition
quality. Do not infer that compositional learning cannot work.

The graph forward pass median was 0.73 ms on valid decoded graphs; warm total
training-task latency was about 0.82 s, dominated by CPU embedding. Fast abstention
on the five confirmation tasks is not useful solving. Receipts and support audit:
`findings/parallel-graph-pilot-v1/`; checkpoint and raw rows remain in the remote run.

## What remains, in order

1. Keep the qualified retrieval/public-check route. Address sibling discrimination
   using development-only negatives and a new natural-absence set, preserving the
   current frozen evaluation. Extend independent stored-solution coverage.
2. Grow independently tested real development compositions and replace the pilot's
   whole-expression bank with parameterized operator/operand prediction. Require
   training support for every admitted part before treating unseen combinations as
   a fair composition test. Keep negatives with counterexamples and accept valid
   alternative graphs. Do not redraw the reserved 66-problem/60-family split.
3. Freeze a sufficiently supported library/data version, then evaluate fresh
   patterns/families once. Report teacher coverage, student first-prediction
   correctness, wrong acceptance and complete latency separately. Compare bounded
   unguided/retrieval-guided search and the generative baseline on matched tasks.
4. No RL campaign yet. The proposed library-growth and pass@8 RL gates remain
   provisional; this pilot does not meet a useful-candidate gate. No new models,
   downloads, Claude runs, or production UI are needed for the next development
   data/compiler work.

## Historical comparison and evidence boundaries

- Final Codex run: 150/150 complete, 121 independently tested problems. Model alone
  and retrieval both 80.2%; templates 77.7%. Claude also gained nothing from the
  tested retrieval route. Do not rank the two models from separate runs.
- V1 held-out audit stopped after 44 problems: 41 demonstrated expressible, 35 via
  generic holes, six algorithm-specific, zero algorithm-specific under 40 nodes.
  Median holes: 58 nodes. Do not resume that exposed set as fresh confirmation.
- Structural mining: 3,207 permitted entries after reserving 66; 2,446 validated
  references, 5,679 clusters, 79 recurring, 44 across families. Repeated structure
  is not an independently verified component.
- Protected test outputs never train the student or enter candidate sandboxes.
  Development independent tests qualify labels; final evaluation tests only score.
  Corpus self-retrieval, test agreement, and benchmark acceptance are distinct.

## Verification and operations

81 focused judge/lane/new-feature tests passed on host 128, plus all 12 existing
synthesis component/grammar tests. macOS cannot run the bubblewrap checks; its
three answer-fixture failures were rerun successfully on Linux. This is focused
verification, not a claim that every Gamma CI or qualification suite ran.

All named runs above completed. No solver/training run is intentionally left
running. The original local Qwen and Claude jobs were not restarted. Check live
processes before resuming anything. Source, data and artifact hashes live in each
run contract; original comparisons and failed receipts remain preserved.

Prior workspace notes, not re-audited here: the legacy plasma/mutecity checkout
reconciliation and root scratch directories remain outside this Gamma task.
