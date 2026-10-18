# Algorithm solver: status and handoff

Updated 2026-10-17. Component: `algorithm_solver`. Intent preserved: fast known
recognition and separately learned, generation-free composition. **The overall
composition goal is not finished.** The current known-answer route has measured
end-to-end evidence; the first composition student has no generalization win.

## Two-button editor integration

The owner clarified the input contract: ASCII is exactly 128 seven-bit entries;
JavaScript and Python are each exactly 256 eight-bit entries, including commands.
`input_fixed_width.py` fits 123 recurring shortcuts from existing screened
training rows; IDs 0–127 remain ASCII and IDs 251–255 are commands. No escape
payloads or extra entries. The previous Huffman profiles remain immutable history.

[Fixed-width receipts](findings/binary-input-byte256-v1/) retain full press costs,
profile/source hashes and prior-exposure limits. Development encoding costs are
192,024/292,152 presses (JS versus ASCII) and 859,040/1,570,219 (Python versus ASCII).
These are ideal encoding counts, not human productivity or solver improvements.

[Editor protocol](editor-protocol.md) now defines the paired loopback bridge,
bounded Python/Node execution and optional known-answer retrieval. The static
256.one UI owns typing and local effort counters; Gamma owns judging and retrieval.
[Workspace evidence](findings/editor-workspace-v1/) records both automated binary
input journeys passing 3/3 public examples and explicit Python answer insertion
without adding manual press counts. Independent tests were not run for these
submitted queries. This does not complete unfamiliar composition or the broader
recognition qualification queue below.

## Two goals

1. Recognize indexed problems despite rewriting and return an existing correct
   solution without generating code. Distinguish siblings, abstain on uncertain
   matches, preserve provenance, and verify the query's public examples.
2. Learned unfamiliar-problem composition: predict solutions by composing typed
   functions, data-structure operations, explicit state and control flow. Reusable
   recipes expand into those building blocks; recipes are not the primitive
   vocabulary itself. A compact neural predictor selects and connects the pieces;
   deterministic code assembles and validates the result without autoregressive
   source generation at runtime. Count retrieval, prediction, assembly and checking.
   Search is a baseline/fallback. The three-algorithm-call limit belongs only to
   the first implemented baseline, not this goal.

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

`call_graph.py` retains the recorded v2 baseline: up to three explicit
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

The 22 qualified teacher graphs, 17/17 training fit and 0/5 confirmation result
describe that bounded baseline. They establish predictor/compiler infrastructure
and missing operator/expression support, not a limit on learned composition.
The distinct finer-grained experiment below tests shared typed pieces and new
connections. No learned unfamiliar-composition success is established until that
system produces protected generalization results.

## What remains, in order

1. Keep the qualified retrieval/public-check route. Address sibling discrimination
   using development-only negatives and a new natural-absence set, preserving the
   current frozen evaluation. Extend independent stored-solution coverage.
2. Grow the frozen typed codec's real development corpus beyond its current
   16 qualified graphs / 12 problems. All admitted operations and recipes occur
   somewhere in this corpus, but support does not survive the proposed family
   split. Add independently tested support across disjoint families. Require
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

## Hierarchical primitive experiment

The user clarified that composition should assemble programming building blocks,
not mostly choose complete algorithms. `typed_program.py`, `typed_recipes.py` and
`typed_experiment.py` now provide a separate, dependency-free development lane.
Lookup, frozen v1 and call-graph v2 are unchanged. Inputs and bindings have types;
comparisons, field projection, arithmetic, collection operations, branches, loops
and accumulation are structured data. DSU, heap, queue and map operations carry
explicit allocation/read/write effects. Four recipes expand hygienically into
the same graph; no arbitrary Python expressions are accepted.

Eight hand-authored variants passed 800 seeded synthetic cases against independent
oracles, both with recipes and after full expansion. The forest oracle exhausts
small spanning forests rather than repeating Kruskal. Both old v2 and the new
representation pass the same 100 minimum-forest cases. Expanded graphs contain
11–29 operations; two three-statement fragments are shared between distinct
recipes with binding identity preserved. Maximum versus minimum forest and
forest weight versus component count each change one graph leaf. These are
representation/edit-count observations, not measured human adaptation effort.

Two type-correct negative graphs have concrete failing inputs. Types establish
structural compatibility, not fulfillment of the requested task. Focused tests
also cover effect order, shadowing, branch scope, resource escape, bounds,
budget exhaustion, fresh state and recipe expansion. 34 focused tests passed,
including the existing v1 synthesis and v2 call-graph checks.

Receipts: [typed primitive development](findings/typed-primitives-dev-v3/summary.json),
with source/input hashes and expanded graphs alongside it. Prediction latency and
first-prediction correctness are **unmeasured**: no model has been trained for this
representation. This is development scaffolding with execution evidence, not a
new unfamiliar-problem solving result. Resources remain local to their recipes;
cross-recipe resource borrowing, recursion and generic container types are not
implemented. List append currently copies the list.

The five examined old confirmation cases are debugging material now. The target
codec freeze and real-development corpus below advance the next step; no student
has been trained on them. Verify feature support in the actual training partition
and reserve fresh protected composition patterns/families before training.
None of these synthetic fixtures is fresh evaluation material. Then teach typed
choices and bindings and score one predicted graph and complete latency; accept
equivalent correct graphs and retain counterexample-backed hard negatives.

## Frozen typed codec and real development corpus

`contracts/typed_codec_v1.json` freezes codec identity `e91aee58…`: typed-program
schema v2, 14 pure operations, **14** stateful operations (adding `map.get`), the
four recipe definitions, types/effects, bindings, expansion, serialization and
limits. Positional invocation uses an explicit ordered `parameters` array;
canonical JSON can sort every object key without changing argument order.
Tests cover nonalphabetical same-type ports through serialization and expansion.
`map.get` returns stored zero rather than a nonzero default, does not insert an
absent key, and rejects boolean/noninteger defaults. `map.has` distinguishes
presence when the stored value equals the default.

The frozen collection/resource capacity is 20,000, allowing the declared
10,000-city bound plus the explicitly unused vertex zero. Qualification uses
a 2,000,000-operation execution budget and the existing Linux sandbox limits.
This is a named bounded profile, not unrestricted runtime support. Prior codec
and synthetic receipts remain historical; the algorithm-call v1/v2 baseline
sources are unchanged.

`typed_pairs.py` now emits source-bound real development targets, provenance,
graph/expansion hashes, required-feature inventories, recipe usage, requirement
reviews, public/independent verdicts and declared-maximum input probes. It rejects
protected or otherwise unpermitted problems before accessing their tests.
Different correct graphs stay together by problem/family/pattern identity.

The final [qualification receipt](findings/typed-real-dev-v2/summary.json) records:

- 16 accepted graphs across 12 selected problems, including four alternative
  implementations; 41 public and 1,884 independent **test executions**, plus
  16 declared-bound probes. Alternative graphs repeat some problem tests.
- Every admitted pure/effectful operation, resource and recipe appears in the
  qualified corpus. This is corpus-wide presence, not split support or learning.
- Four explicit exclusions for mandatory complexity, missing operations or
  unsupported input bounds. No incorrect-answer fit was accepted to bypass them.
- Two type-correct negatives have failing public counterexamples.
- 81 focused tests and 816 subtests passed on host 128. The run used an isolated
  source snapshot at `09dad3af2`, preserving the remote checkout's concurrent work.

The initial [run](findings/typed-real-dev-v1/summary.json) qualified 14 graphs and
failed Missing Number and Redundant Connection. Tracing found invalid imported
suites: 7/47 Missing Number cases violated the value domain; 62/76 Redundant
Connection cases violated endpoint or single-cycle graph constraints. Their
original files, outputs and failure receipts remain unchanged. A source-hash-bound
development repair rejects those suites as qualification authorities and supplies
336 set-difference-oracle cases and 170 edge-removal/connectivity-oracle cases.
These are separately identified development tests, not benchmark rescoring.
Details: [test integrity](findings/typed-real-dev-v2/test_integrity.json).

The [support audit](findings/typed-real-dev-v2/support_audit.json) still blocks the
proposed split: only 2/6 audit targets have complete support in its 10 fit targets;
the split places every DSU example outside training. In leave-one-family-out
diagnostics, 7/12 families have full feature support. Do not present that split as
a fair generalization experiment or train against it. All examined targets remain
development/debugging material. Fresh protected patterns/families have **not**
been reserved for this codec; no new predictor, search comparison, or generalization
result is claimed. Build cross-family support before that reservation and training.

## Binary-input vocabulary study (256one integration)

The user also requested corpus-derived input vocabularies and challenge navigation.
This is an encoding study, not additional solver correctness evidence. Source
acquisition, fitting and metadata export live in `algsolve/input_corpus.py`,
`input_vocabulary.py` and `input_catalog.py`; the browser remains in 256one.
See [the retained receipt](findings/binary-input-v1/python-summary.json).

Pinned Doocs sources (657 JavaScript and 3,418 TypeScript files, plus license and
README) remain under ignored `data/raw/doocs__leetcode_input/<revision>/` on host
128, with per-file Git blob and SHA256 verification. They have not been executed.
Python v1 fits 128 shortcuts on 1,831 permitted validated ASCII reference texts
and scores 466 separate family-split development files: 609,096 presses versus
1,570,219 for ASCII, a 61.2% ideal encoding reduction. This does not measure human
speed, prove optimal vocabulary selection, or change the frozen solver vocabulary.
Protected solving/recognition/reserved families remain excluded via the existing
training policy. Raw rows and profiles stay in `runs/binary-python-v1/`.

The challenge export contains only titles, slugs and difficulties for 3,353 known
problems. It is navigation, not an editor judge or deployed solver. Next: evaluate
a JS successor using the pinned sources, count corrections/navigation effort,
and compare fixed candidate vocabularies before replacing already learned codes.
