# Evaluator-isolated failure ledger on the sealed literal-margin fit captures

Track A step 2 of the combined Gamma plan. [ledger.py](ledger.py) runs two
physically separate phases on Jupiter (host 128, `.venv_rocm`):

1. **Solver** — the ten sealed captures of `runs/typed-literal-margin-fit-128-v1`
   replayed through the guard experiment's control, semantic and guarded
   candidate routes (instrumented source, `2fc844d57` plus this driver). The
   full solver records are sealed ([solver-seal.json](solver-seal.json))
   before any evaluator data is opened. Records include timings, so their hash
   differs between runs; decisions do not.
2. **Evaluator** — witnesses (the qualified fit targets), independent tests and
   training exposure, joined after the seal. Every route is scored; failures
   get observed evidence (decode rejections, public disagreement, budget),
   field differences against the nearest witness on meaningful cells only, and
   controlled attribution experiments substituting one field class of the
   witness into the solver's candidate.

Attribution strength: **observed** (recorded by the solver), **controlled
repair** (substituting one declared field class makes the candidate
independently correct — a sufficient correction here, not a unique cause),
**hypothesis** (not isolated). Training exposure: all ten are consumed fitting
problems; per-alternative contribution was not retained and stays unknown.

## Results ([evaluator-ledger.json](evaluator-ledger.json))

| Route | Accepted correct | Wrong acceptances | Abstained but correct |
|---|---|---|---|
| control | 4 | 0 | 0 |
| semantic | 7 | 0 | 0 |
| candidate (guarded) | 8 | 0 | 0 |

These reproduce the retained guard experiment. Every control failure differs
from its nearest witness in one field class only, and substituting that class
alone repairs it (controlled repair):

| Problem | Class | Cells | Values (solver → witness) | Recovered by existing repair |
|---|---|---|---|---|
| lcd:1464 | operation | 1 | recipe:stable_unique → recipe:heap_sort | yes (recipe) |
| lcd:1046 | literal | 1 | 0→2 | yes (bit flip) |
| lcd:2144 | literal | 2 | 0→2, 2→3 | yes (bit flip, guarded) |
| lcd:1710 | literal | 2 | 0→1, 0→1 | yes (bit flip) |
| lcd:1101 | literal | 3 | 1→−1, 0→2, 0→1 | no: needs 3 edits (limit 2) |
| lcd:1489 | literal | 7 | five 0→2, two 1→0 | no: 7 edits, beyond any two-bit search |

Each differing literal is off by exactly one bit and lies in −1..3.

## Limits

Consumed fitting problems; the checkpoint trained on them. The literal
pattern above was observed before any value-proposal policy was designed, so a
policy evaluated on these ten cases is development evidence only and needs
fresh captures before any broader claim. Replay excludes embedding and
inference (not latency evidence).
