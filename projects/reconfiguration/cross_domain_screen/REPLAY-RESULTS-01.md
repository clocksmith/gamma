# Corrected sealed-output replay

Exploratory verified evaluator repair on existing sealed samples, not confirmation. Original scores retained separately; no broad transfer or efficiency claim.

The [replay receipt](screen-run-01/oracle-replay-v2.json) binds all inputs and
changed checks. The [original restricted-grammar report](RAW-RESULTS-01.md)
remains preserved alongside the [raw archive](screen-run-01/archive.json).

Versioned syntax interpretation/expansion: allow bounded pure inline lambdas and ordinary sorted key/reverse keywords. The prompt allowed sorted but did not explicitly specify inline lambda/keyword support; the original restricted grammar is preserved. Behavioral expected cases, exact answers, strict output formatting and pass combination remain unchanged.

| Condition | Original restricted semantic pass | Corrected behavioral semantic pass | Corrected wrong acceptances |
| --- | ---: | ---: | ---: |
| base | 4/6 | 4/6 | 2 |
| channel_gain | 4/6 | 4/6 | 2 |
| shuffled_context | 4/6 | 4/6 | 2 |
| permuted_gain | 3/6 | 4/6 | 2 |

Replayed all 24 original sealed outputs. New model/GPU calls: 0. Changed score
records: 1 (`python-intervals/permuted_gain`). Original generation costs are
unchanged; CPU replay wall time was 5,185.130 ms (5.185 seconds).

Paired corrected outcomes against base:

- channel_gain: 0 wins, 0 losses, 6 ties.
- shuffled_context: 0 wins, 0 losses, 6 ties.
- permuted_gain: 0 wins, 0 losses, 6 ties.

The repaired scores show no gain advantage on these six families.

[Original oracle](oracles.py) SHA256: `a1f36a3f613e5f4a6a13fcf0604de49ab69baaa855826933a0e824ff85d9c364`.
[Versioned oracle](oracles_v2.py) SHA256: `8264910252460e4b5257cb8d13365470a88e6e8d1f261f1be567300f9e8af743`.
Original outputs seal: `10f81e8c2f5be07827f13a30afc0fdff52f2b4aee2152493aaa484c77e79401e`.
Replay: `e78a328076daa3a6c56af43526f3da091ecc6b519058e261bbd35ca335acfd92`.
