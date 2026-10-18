# Algorithm solver lane

A bounded experiment: can known-answer lookup, retrieved examples, or an
algorithm-pattern classifier with templates make a small local model
(Qwen3.5-4B, thinking off) faster or more reliable than the same model alone?

Results are labelled "held out from our pipeline; prior model exposure
unknown" and describe one model, one backend and one budget. They are an
initial comparison, not a ranking.

## Routes

| Route | What the model sees |
|---|---|
| `lookup` | nothing; a stored solution is returned only if the lookup matches and passes the public examples |
| `model_alone` | the problem (control) |
| `retrieval` | the problem plus the two most similar solved index problems |
| `classify_template` | the problem plus templates for up to two predicted patterns |

Generative routes get the same token caps, one repair (public-example feedback
only) and one 120 s wall-clock limit. See `contracts/run_contract.json`.

## Commands

All commands run from this directory with `gamma/.venv_rocm/bin/python`.

```bash
python -m algsolve.fetch                          # approved downloads, hash manifest in data/raw/
python -m algsolve.prepare inspect                # import, validate references, embed, list near-duplicates
python -m algsolve.prepare freeze                 # drop near-duplicates, freeze contracts/sample_manifest.json
python -m algsolve.prepare decode                 # decode LiveCodeBench hidden tests inside the sandbox
python -m algsolve.run --run-name baseline-v1     # fit, recognition, solving, report (resumable)
python -m algsolve.run --run-name baseline-v1 --stages report
```

`run` refuses to start unless the manifest is committed and matches the
contract hash, the GPU probe passes, and the judge self-check rejects hanging
and networked candidates.

## Data

| Source | Use | License note |
|---|---|---|
| newfacade/LeetCodeDataset | index (train), solving and absent queries (test) | apache-2.0 / MIT (conflict recorded) |
| doocs/leetcode @ 88c8c2c | index statements, tags, reference solutions | CC-BY-SA-4.0; commercial reprints need authorization; research use only |
| livecodebench/code_generation_lite test6.jsonl | solving | card "cc" / loader MIT |
| open-r1/codeforces verifiable test split | solving (21 complete-test problems, rest example-level) | cc-by-4.0 / ODC-By 4.0 |
| open-r1/codeforces-submissions selected_accepted | fetched; 4 sampled-pool problems have Python submissions, so unused | see card |

Fetched and derived data stay under `data/` (gitignored); run outputs under
`runs/` (gitignored). Nothing here is redistributed.

## Layout

- `algsolve/judge/`: bubblewrap sandbox, in-sandbox harness, host-side verdicts
- `algsolve/importers.py`, `values.py`: normalized records; tests parsed by an AST whitelist, never executed on the host
- `algsolve/validate.py`: references must pass their own tests before a problem is eligible
- `algsolve/splits.py`, `prepare.py`: index, aliases, near-duplicates, frozen sample
- `algsolve/lookup.py`, `classify.py`, `patterns/catalog.py`, `routes.py`, `model.py`: the four routes
- `algsolve/run.py`, `report.py`: the comparison command and the report rebuilt from results

## Learned composition target (current direction)

The newest representation experiment is
[typed primitives and expandable recipes](#typed-primitives-and-expandable-recipes).
The older pilots below remain evidence; they are not the intended final component
granularity or a qualified unfamiliar-problem solver.

The active two-track goals and measured gaps are in [STATUS.md](STATUS.md).
For unfamiliar problems the selected experiment is non-autoregressive,
retrieval-conditioned graph prediction: interacting slots predict component IDs
(including EMPTY), input/earlier-output bindings, bounded parameters and structure.
Deterministic code validates and compiles the proposal. Search is a matched
baseline and bounded fallback. Measure the first prediction before retries;
retrieval, prediction, assembly and verification all count toward complete latency.

`algsolve/synth/graph_targets.py` supplies a bounded target representation and
compiler over frozen vocabulary v1, not a neural model. Initial targets use
functional IO, three stage slots, explicit bindings, structured hole ASTs and
<=40 total hole AST nodes with at least one algorithm-specific skeleton.
`training_pairs.py` exports only permitted development proposals that round-trip
without changing their rendered program and freshly pass public and independent
tests. It does not trust old audit pass labels, import the all-corpus service index,
call a model, train weights or expose hidden test contents as model inputs.

```sh
python -m algsolve.synth.training_pairs --audit runs/audit-dev-1/audit.jsonl --audit runs/audit-dev-1-recheck/audit.jsonl --audit runs/audit-dev-1-recheck2/audit.jsonl --confirmation findings/mine-v2-candidates-20261017/split.json --name graph-targets-v1
```

Run under the existing Linux sandbox environment. Output is a new immutable
`runs/<name>/` containing a contract, pairs and summary. Source problem identities,
license/attribution, vocabulary identity and fresh validation provenance are
retained. Connected groups of problem identities and structural graph patterns
are assigned together; hash-selected groups are reserved for pattern confirmation.
This conservative structural grouping is not proof of semantic-pattern novelty.
A tiny export is not enough to qualify the proposed model. The separate
`call_graph.py` candidate now exposes existing library algorithms as explicit
nodes and adds independently tested fixed-width window sums. Of 23 selected
development proposals, 22 pass fresh public/independent tests within the
40-node glue limit. This is selected teacher coverage, not benchmark coverage.

`parallel_graph.py` and `train_parallel.py` implement a retrieval-conditioned
parallel slot predictor, deterministic assembly and a frozen development pilot:

```sh
python -m algsolve.synth.call_graph_pairs --proposals contracts/call_graph_development.json --confirmation findings/mine-v2-candidates-20261017/split.json --name call-graph-dev-v2-requalified
python -m algsolve.synth.train_parallel --dataset runs/call-graph-dev-v2-requalified/pairs.jsonl --name parallel-graph-pilot-v1 --steps 200
```

Use new names for new executions; existing datasets/runs are not overwritten.
The pilot passed 17/17 training tasks and 0/5 pattern-confirmation tasks. Four
confirmation graphs need expression templates missing from training and three
use operators without training examples; none has complete training support.
The 149,505-parameter graph head runs alongside a frozen 0.6B embedding model.
It is working model/compiler infrastructure, not qualified unfamiliar solving.
See `findings/parallel-graph-pilot-v1/` and the current next steps in `STATUS.md`.
More verified real compositions, parameterized expression prediction, hard
negatives and fresh supported confirmation remain necessary.

Research precedent, not Gamma evidence: [NAPG](https://arxiv.org/abs/2211.03462)
reports 21x faster program generation on ConvFinQA/MultiHiertt numerical QA.
[Syntax-tree diffusion](https://arxiv.org/abs/2405.20519) demonstrates iterative
syntax-preserving editing for inverse graphics. Neither result establishes
Gamma algorithm-solving speed or coverage. Refinement/diffusion must justify
its additional passes on this workload.

## Typed primitives and expandable recipes

This separate experiment implements the requested finer granularity before more
training. `algsolve/synth/typed_program.py` interprets typed JSON graphs with pure
operators, explicit stateful calls, lexical bindings, branches, bounded iteration
and accumulation. A recipe expands into that same representation. There are no
Python source holes or hidden complete-algorithm calls in the expanded graph.

The initial catalog has 14 pure operations, 13 effectful operations over DSU,
integer heap/queue/map resources, and four inspectable recipes. `forest` expands
to sort edges, project endpoints/weight, find roots, compare, conditionally union,
and accumulate. `cycle_weight` changes the connections and sums rejected edges.
Heap sort and stable uniqueness can be connected in either order; equivalent
correct graphs are accepted. Types and state effects do not establish task
correctness: two intentionally wrong, type-correct graphs retain counterexamples.

From `projects/algorithm_solver`, with no model or new dependencies:

```sh
python3 -m algsolve.synth.typed_experiment --output runs/typed-primitives-new-run
```

The command refuses to overwrite a run. It writes source/input-bound contracts,
graphs (including expanded forms), case rows, and a summary. The retained
[development receipt](findings/typed-primitives-dev-v3/summary.json) records eight
variants and 800/800 small synthetic cases passing independent oracles. Expanded
sizes are 11–29 operation nodes; refs/literals are not counted as operations.
There are two shared three-statement fragments across distinct recipes, preserving
reference identity under binding renaming. This is measured structural reuse in
hand-built examples, not discovered corpus coverage.

The matched minimum-forest comparison also runs the retained v2 Kruskal graph.
Timing distinguishes old execution alone from complete assembly and new typed
validation/execution. Neither includes retrieval, prediction, or external judging.
Prediction time and first-prediction correctness are null because no predictor
targets this representation yet. Graph leaf changes are an adaptation proxy,
not human-action measurements. Inputs are small, resources are recipe-local,
and functional append copies lists; this is not a performance-qualified runtime.

All examples and the five previously examined confirmation problems are now
development/debugging material. The next learning experiment must check target
expressibility and training coverage before training, then use fresh protected
patterns/families. The existing known-problem lookup path is untouched.
