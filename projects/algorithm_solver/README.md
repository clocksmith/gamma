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
A tiny export is not enough to train or qualify the proposed model. Retrieval
conditioning, synthetic target generation, hard negatives and a trained predictor
remain to be implemented and evaluated against protected tasks.

Research precedent, not Gamma evidence: [NAPG](https://arxiv.org/abs/2211.03462)
reports 21x faster program generation on ConvFinQA/MultiHiertt numerical QA.
[Syntax-tree diffusion](https://arxiv.org/abs/2405.20519) demonstrates iterative
syntax-preserving editing for inverse graphics. Neither result establishes
Gamma algorithm-solving speed or coverage. Refinement/diffusion must justify
its additional passes on this workload.
