# M1 cost decomposition and optimistic bound

[Frozen design](FREEZE.md), pushed in `2523d591c` before measurement. [Evidence](evidence/results.json) contains only IDs, hashes, counts and aggregates. Sources, dictionaries and sequences remain private.

The largest remaining category is **syntax**. On L-R-256 dev-val it accounts for 4488.85/8948 byte-fraction-attributed selections (50.2%). These are descriptive attributions; deleting a category would require resegmentation and can change correctness.

The optimistic lower bounds do **not** establish M1 feasibility or impossibility. They leave substantial room below the current codebook. Local search stopping and general-compressor rates do not close that gap. M1 remains unchanged and unmet.

## Measured baseline

| Development split | Entries | Selections | Median | p95 | Single-character | Actions incl. Finish | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dev_fit | 128 | 41,684 | 107.0 | 303 | 79.2% | 41,984 | 49,725 |
| dev_fit | 256 | 26,108 | 68.0 | 188 | 54.1% | 26,408 | 40,615 |
| dev_val | 128 | 14,014 | 103.5 | 320 | 78.7% | 14,114 | 17,225 |
| dev_val | 256 | 8,948 | 63.5 | 211 | 55.1% | 9,048 | 15,255 |

Both dev-val selection totals reproduce the prior L-R baselines exactly. All 800 packets decode to the pinned R source hashes. Existing source qualification is reused; no new execution/correctness or numerical qualification is claimed. Only the 400 explicit development source paths were opened.

## L-R-256 dev-val attribution

| Category | Fractional selections | Share | Single-character selections | Share of tail | Source bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| identifier | 3495.22 | 39.1% | 2378 | 48.2% | 9860 |
| literal | 963.93 | 10.8% | 685 | 13.9% | 1566 |
| syntax | 4488.85 | 50.2% | 1871 | 37.9% | 14566 |

A2 failed: syntax leads total attributed selections, but identifiers lead the single-character tail. Mixed selections are split by byte overlap; the integer exclusive/mixed partition is in the evidence. Single-character attribution is exact integer accounting. Property names count as identifiers.

| Syntax detail | Fractional selections | Single-character selections |
| --- | ---: | ---: |
| delimiter | 2329.95 | 1003 |
| keyword | 431.69 | 35 |
| layout | 173.84 | 29 |
| operator | 1553.37 | 804 |

## Optimistic bounds

| Scope | Programs | Lower total selections | Lower median | Lower p95 |
| --- | ---: | ---: | ---: | ---: |
| Arbitrary shared dictionary <=128, capacity relaxation | 400 | 4027 | 9.5 | 23 |
| Arbitrary shared dictionary <=256, capacity relaxation | 400 | 1821 | 2.0 | 13 |
| Fit-witnessed substrings only, unlimited union on dev-val | 100 | 2761 | 21.0 | 75 |
| Cross-program strings only, unlimited union; diagnostic | 400 | 10184 | 18.0 | 65 |

The capacity bound applies to arbitrary shared dictionaries for these **fixed 400 sources**, not all equivalent programs or the full 500 qualification. At most K programs can benefit from private multi-character entries in a K-entry dictionary. The bound optimistically lowers those programs to two selections and makes every shared substring available without consuming slots. This drops shared-slot competition and is deliberately weak. Its median cannot rule out 32 when K=256 on 400 programs. It is a necessary bound, not an attainable dictionary.

The fit-transfer oracle applies only to literals witnessed in fit (plus characters); designed unseen strings can beat it. The cross-program diagnostic uses validation text retrospectively and is not a fitted-vocabulary score. Both relax shared cardinality and whole-body exclusions. Whole-program exclusion supplies the two-selection floor. No single-character feasibility claim follows; its universal optimistic lower bound is zero.

One Finish adds one to each action bound. Payload uses 7/8 bits per selection; packets also charge padding and 41-byte headers. Dictionary storage and codec source bytes are separate in evidence. Codec source size is not a full runtime-footprint measurement.

## Predictions, checks and next action

| Prediction | Outcome |
| --- | --- |
| A1 | Met |
| A2 | Not met |
| A3 | Met |
| A4 | Met |
| A5 | Met |

Six synthetic tests passed, including exhaustive tiny-dictionary lower-bound ordering, suffix-oracle comparison against brute force, mixed-span conservation and allowlisted loading. Python compilation passed. The existing judge/lane tests passed **37/37** using the existing `.venv_rocm` pytest runtime; no dependency was installed. The measurement itself uses system Python and Node, with one worker.

Measured analysis wall time: 0.742 seconds. Review and launch receipts are recorded in [REVIEW.md](REVIEW.md).

Next: board item 3 is claimed for a matched conventional dictionary experiment targeting the syntax tail, retaining the existing fit/validation separation, exact charging and baseline. A bound gap alone is not evidence that stronger search or a learned scorer will find a gain. No training is authorized.

Rebuild this report from a complete private run with:

```sh
python3 -B projects/algorithm_solver/literals/cost-decomposition-v1/report.py --run /path/to/cost-decomposition/run-v1
```

Component: algorithm_solver literal research. Intent preserved. No production boundary changed; no held-out/protected opening, BITS deployment, private-source publication, ledger/catalog/claim write, human-study outcome or autonomous-solving claim.
