# Full-substring character-fraction certificate

[Freeze](FREEZE.md); [resource amendment](AMENDMENT-1.md); [review](REVIEW.md); [derivation](DRAFT.md); [metadata evidence](evidence/results.json).

Private sources, substring pools, multipliers, dictionaries and packet sequences are not published.

Neither start-tied certificate is positive. The full-substring fraction question remains unresolved unless an exact decoded witness below reaches F <= 0.

The objective is F = 10C - T, where C counts single-character selections and T counts all eight-bit selections. The candidate class contains every occurring nonempty exact substring at every length, including one-owner entries, except exact fit source/body bans. Every entry consumes one of 256 optional dictionary slots.

| Cohort | Distinct words / groups | Exact numerator / denominator | Integer bound | Best feasible F | Excludes 10% | Iterations / stop |
| --- | ---: | --- | ---: | ---: | --- | --- |
| R | 13,553,771 / 111,543 | -37980000000 / 1000000 | -37980 | 110156 | False | 2000 / iteration_limit |
| naming | 13,561,646 / 111,543 | -37943000000 / 1000000 | -37943 | 94121 | False | 2000 / iteration_limit |

The full primal substring space is covered, but the dual search ties all multipliers at a source start. Long one-owner suffix groups contain many lengths with the same activation weight; top-256 subtraction can spend many activations on those same starts. A nonpositive bound may reflect this restricted dual family. It does not prove that an actual dictionary reaches the target or that the full substring representation has failed. A positive bound remains valid for all dictionaries and segmentations in the stated fixed-source class.

| Cohort | Witness | Entries / one-owner | Selections | Median / p90 / p95 / worst | Character fraction | F | Package / with decoder source bytes |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| R | best | 249 / 3 | 28554 | 74.5 / 180 / 199 / 964 | 48.58% | 110156 | 43026 / 56036 |
| R | seed | 249 / 3 | 28554 | 74.5 / 180 / 199 / 964 | 48.58% | 110156 | 43026 / 56036 |
| naming | best | 249 / 3 | 27099 | 71.0 / 166 / 193 / 918 | 44.73% | 94121 | 41584 / 54594 |
| naming | seed | 249 / 3 | 27099 | 71.0 / 166 / 193 / 918 | 44.73% | 94121 | 41584 / 54594 |

Every witness packet was independently parsed into eight-bit IDs, reconstructed, matched to the exact min-F encoder and qualified source hash, and fully recounted. The encoder minimizes F, then selection count and dictionary IDs; this is not minimum-ratio or minimum-selection encoding. Costs include one Finish action, 41 framing bytes per program, dictionary bytes and decoder source bytes. Evidence contains per-program costs, entry lengths, distinct-program support and actual packet usage, without entry strings.

| Cohort | Witness | Min / median / max entry length | Entries >=90% of a containing source | Unused entries | Character entries |
| --- | --- | --- | ---: | ---: | ---: |
| R | best | 1 / 2 / 39 | 0 | 17 | 89 |
| R | seed | 1 / 2 / 39 | 0 | 17 | 89 |
| naming | best | 1 / 2 / 39 | 0 | 15 | 89 |
| naming | seed | 1 / 2 / 39 | 0 | 15 | 89 |

The 90% size statistic describes near-whole entries; it is not a semantic legality test. Exact bans can still admit near-whole or disguised task-specific chunks. All witnesses remain relaxation witnesses with semantic reuse unassessed. Even an F <= 0 witness does not establish M1 reusable-library legality, quantile targets, 400-of-500 coverage, source-rewriting limits, human fluency or autonomous solving.

| Cohort | Proposals / infeasible | Pool construction / ascent and replay / total arm seconds |
| --- | ---: | --- |
| R | 160 / 160 | 1.58 / 304.11 / 306.60 |
| naming | 160 / 160 | 1.52 / 305.98 / 308.44 |

1200 witness packets replayed; whole-job wall time 308.60 seconds. The report reconstructs the suffix index and exact bans, verifies full interval/depth coverage, and checks exact integer path/top-256 accounting using independent partition validation and segment-tree replay. No optimizer is run by this reporter.

| Prediction | Definition | Met |
| --- | --- | --- |
| P1 | Both arms complete a verified certificate within hard caps | True |
| P2 | At least one positive bound (low-confidence hypothesis) | False |
| P3 | Neither generated dictionary reaches F <= 0 | True |

Later unchanged-source qualification exited 137; this exact item 13 hash reuse does not erase that failure.

Qualification here reuses exact item 13 source hashes. It does not replace that failure with a new runtime receipt. Validation and protected source values remain unopened. The complete installed interpreter/library footprint is unmeasured. Component intent and production boundaries are unchanged; no promotion or milestone readiness is claimed.

Rebuild using the pinned Python with `report.py --run /private/all-substring-fraction/run-v1 --work /private/literal-admission500-v1`. Synthetic reporter checks are available with `report.py --self-test`.
