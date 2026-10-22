# style150-v2: frozen design

Successor to [style150-v1](../style150-v1/README.md), fixing the search confound it found.
[contract.json](contract.json) pins the code and the v1 contract. Committed before any v2 arm ran.

The single change: [measure.py](measure.py) scores candidate spans on each problem's chosen
source only. v1's joint-v1 span proposer counted every variant in the pool, so with several
verbose variants per problem its shortlist filled with whitespace runs from unchosen sources.
Everything else is v1's: population, existing pool (998), the 150 qualified rewrites, D0
start dictionaries, held-out split, neighborhood, and the 100,000-trial cap (4-hour safety
limit) per search arm.

Arms C, D, E, CH and DH, at 128/7 and 256/8 (definitions in the v1 freeze).

## Predictions

- Q1: at 256 entries, D uses no more selections than E (its pool is a superset).
- Q2: at 256 entries, D uses at least 10% fewer selections than C.
- Q3: on the held-out 30 at 256 entries, DH uses at least 10% fewer selections than CH.
- Q4: at 256 entries, CH and DH end with more than 128 entries.
- Q5: at 256 entries, D uses fewer selections than v1's E (9,538).

## Disclosure

Before freezing, the fixed proposer was checked on v1's stalled CH-256 state (an existing v1
output). Its top candidates (`while(`, `.push(`) each save hundreds of selections there,
whereas v1's proposer offered only zero-gain whitespace. No v2 arm had run.

Plumbing amendment: the first launch failed before any arm ran (the process pool could not
pickle v1's dynamically loaded `run_arm`). `measure.py` now submits a module-level wrapper and
the contract hash was updated; no design, budget or prediction changed.
