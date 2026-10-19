# Matched typed-composer development comparison

Candidate: `4621bbb95ad87d5db4d2251bd58c2bf6fde8005242550f359befa6157e650749`.

Disposition: **rejected_or_incomplete; protected_scoring_closed**.

| Partition | Route | Cases | Valid | Accepted correct | Wrong accepted | Abstained | Total p50 / p95 (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| development_fit | raw | 10 | 8 | 4 | 0 | 6 | 1.0917 / 1.9746 |
| development_fit | constrained | 10 | 9 | 4 | 0 | 6 | 1.1146 / 1.9762 |
| development_fit | nearest_training_graph | 10 | 10 | 8 | 0 | 2 | 1.1057 / 1.9718 |
| development_audit | raw | 8 | 0 | 0 | 0 | 8 | 0.7131 / 0.9694 |
| development_audit | constrained | 8 | 0 | 0 | 0 | 8 | 0.8837 / 1.0939 |
| development_audit | nearest_training_graph | 8 | 4 | 0 | 0 | 8 | 0.7273 / 0.9882 |

Correction outcomes (useful / harmful / unchanged / neutral / unknown):

- development_fit: 0 / 0 / 9 / 1 / 0
- development_audit: 0 / 0 / 8 / 0 / 0

Selection checks:

- nonempty_partitions: pass
- correctness_gain: fail
- no_harm: pass
- wrong_acceptances: pass
- validity: pass
- abstention: pass
- latency: pass
- fit_preserved: pass
- infrastructure: pass

Reproduce on the qualified Linux host with the sealed dependencies and original assets:

```sh
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.compare_typed --name NEW-UNUSED-RUN
```

The runner refuses changed checkpoints or codecs. `candidate.json` pins the complete source, dependency, data and configuration identity. `captures.jsonl` retains raw predictions and logits. `decisions.jsonl` fixes every route response before independent scoring; `scores.jsonl` adds separate execution verdicts. `summary.json` retains artifact hashes and phase setup costs. Each completed route score is retained under `scoring/`. Resume an interrupted scoring stage with the same `--name` and `--resume-scoring`; changed candidates, decisions or scoring identities are rejected.

No protected cases or fresh 2b variants were scored. This report does not authorize the autonomous loop.
