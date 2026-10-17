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
