# CATSCAN: Benchmarking

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Produce matched, traceable measurements for named models, engines, and workloads.

## Authority

- Owns benchmark execution, timing boundaries, statistics, workload identity, and comparison receipts.
- Does not own engine behavior or generalize a narrow result beyond its workload.

## Scope

- Applies to benchmark execution, timing boundaries, statistics, workload identity, and comparison receipts.

## Contracts

- Input: Explicit engine, model, workload, sample, warmup, and metric contracts.
- Output: Raw observations and derived statistics with enough provenance to replay the comparison.

## Invariants

- Compared rows perform equivalent named work under compatible timing scopes.
- Warmup and timed samples remain distinguishable.
- Missing, asymmetric, or fallback work makes a comparison non-promotable.

## Acceptance

- Statistics and performance telemetry remain deterministic from their raw rows.
- Evidence: [statistics tests](../../tests/test_statistics.py), [KV-cache latency tests](../../tests/test_kv_cache_latency.py), and [benchmarking guide](../../docs/BENCHMARKING.md).

## Non-goals

- Manufacturing a winner by changing work, scope, or missing-value policy.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
