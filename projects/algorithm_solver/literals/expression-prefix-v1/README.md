# Prefix expression constructors on fixed R sources

[Freeze](FREEZE.md) pushed in `9e83e182c`; [review and run receipt](REVIEW.md); [sanitized evidence](evidence/results.json).

Input candidate: **none**. Goal 2c is a separate representation track. These consumed-development results do not qualify M1 or autonomous assembly.

The 128-entry typed arm saves 181 validation actions (1.28%) versus its searched literal control; the 256-entry arm saves 42 (0.46%). Neither passes the frozen readiness criteria. The 128-entry literal search itself regresses by 80 validation actions versus the pinned baseline, so its typed gain is 101 actions versus that baseline. Conditional eligibility covers 99 of 100 validation programs; actual constructor use is narrower. These are small measured benefits, not an impossibility finding.

## Costs

| Entries | Arm | Split | Selections | Median / p90 / p95 / worst | <=32 / <=96 | Actions | Single-char | Constructor codes / programs | Raw package | With decoder dependencies |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: |
| 128 | literal | fit | 41680 | 107.0/257/303/1173 | 10/129 | 41980 | 79.35% | 0/0 | 49720 | 62730 |
| 128 | literal | validation | 14094 | 105.0/267/320/716 | 6/42 | 14194 | 79.01% | 0/0 | 17300 | 30310 |
| 128 | typed | fit | 41237 | 107.5/256/294/1170 | 10/128 | 41537 | 77.87% | 857/177 | 50215 | 295989 |
| 128 | typed | validation | 13913 | 103.0/263/323/704 | 6/44 | 14013 | 77.47% | 289/57 | 18021 | 263795 |
| 256 | literal | fit | 26108 | 68.0/162/188/930 | 48/216 | 26408 | 54.06% | 0/0 | 40615 | 53625 |
| 256 | literal | validation | 8948 | 63.5/169/211/501 | 13/69 | 9048 | 55.14% | 0/0 | 15255 | 28265 |
| 256 | typed | fit | 25995 | 67.0/161/184/930 | 49/215 | 26295 | 53.99% | 230/73 | 41909 | 287683 |
| 256 | typed | validation | 8906 | 63.0/168/209/501 | 13/70 | 9006 | 54.88% | 66/21 | 16620 | 262394 |

All four arms decode 400/400 packets exactly to their pinned source hashes. Source bytes are unchanged; existing qualification is reused. No fresh execution, unseen-correctness or generalization claim. One Finish is included per program. Every constructor and child consumes a code; prefix arity supplies boundaries. Dictionary metadata, 41-byte headers and padding are charged.

Decoder dependencies count the typed decoder and Acorn source, or canonical literals.py and bitpack.py. Complete installed Node/CPython/stdlib footprints remain unmeasured. Raw and decoder-inclusive costs are separate; neither establishes storage dominance without its relevant accounting scope.

## Conditional validation contrasts

Eligibility is any match from the sealed fit constructor pool, before dictionary selection outcomes. Actual constructor use is reported separately above. All contrasts are typed minus the matched searched literal arm.

| Entries | Subset | Programs | Typed / literal actions | Delta | Better / same / worse |
| ---: | --- | ---: | --- | ---: | --- |
| 128 | all | 100 | 14013/14194 | -181 | 37/48/15 |
| 128 | eligible | 99 | 14002/14183 | -181 | 37/47/15 |
| 128 | complement | 1 | 11/11 | 0 | 0/1/0 |
| 256 | all | 100 | 9006/9048 | -42 | 38/51/11 |
| 256 | eligible | 99 | 8998/9040 | -42 | 38/50/11 |
| 256 | complement | 1 | 8/8 | 0 | 0/1/0 |

## Search and readiness

| Entries | Arm | Constructor entries | Trials | Rounds | Stop | Search seconds | Decoder bytes |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 128 | literal | 0 | 1217 | 1 | local_optimum | 87.11 | 13010 |
| 128 | typed | 2 | 3909 | 3 | local_optimum | 297.46 | 245774 |
| 256 | literal | 0 | 737 | 0 | local_optimum | 36.70 | 13010 |
| 256 | typed | 1 | 6661 | 5 | local_optimum | 373.58 | 245774 |

Matched arms share starting dictionaries, proposal rules and the fixed expression-literal pool. Their selected-span merge proposals can diverge with their parses. A time or trial cap limits the search contrast; termination does not establish global optimality or constructor impossibility.

- 128: 1.28% fewer validation actions; ready=False; failed predicates: actions_5_percent, improved_60.
- 256: 0.46% fewer validation actions; ready=False; failed predicates: actions_5_percent, improved_60, package_within_105_percent.

| Prediction | Met |
| --- | --- |
| X1 | True |
| X2 | True |
| X3 | False |
| X4 | True |
| X5 | True |
| X6 | True |

Measured run wall time: 375.15 seconds. Nine synthetic tests and Python compilation passed before launch. Initial literal parsing reproduces both pinned baselines. Per-program packet/source hashes and one-program storage, full action distributions, pool eligibility, entry size/reuse, framing and padding are in the evidence. Search traces, source bodies, dictionaries, packets and cases remain private.

Next work must be separately frozen. Any confirmation opening, training, publication of source rewrites, BITS deployment or human study remains owner-gated. Component: algorithm_solver literal research; intent preserved. The new decoder grammar is isolated from canonical literals and production. No M1 threshold, ledger/catalog/claim or live-profile change.

Rebuild: `python3 -B projects/algorithm_solver/literals/expression-prefix-v1/report.py --run /private/path/to/expression-prefix/run-v1`.
