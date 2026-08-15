# CATSCAN: SAME-R

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Attribute outcome differences to swappable approaches under matched evaluation and replication contracts.

## Authority

- Owns SAME-R contract schemas, experiment registration, selector rules, and replication evidence.
- Does not declare a benchmark valid or a result general beyond its contract.

## Scope

- Applies to SAME-R schemas, experiment registration, selector rules, and replication evidence.

## Contracts

- Input: Validated [contract suites](contracts/same-r-contract-suite.schema.json) and registered experiment identities.
- Output: Matched experiment plans, receipts, selector decisions, and replication records.

## Invariants

- Objective, control, benchmark, success metric, and replication contract stay fixed across compared approaches.
- Missing antecedents fail closed.
- Selection evidence remains separate from final replication evidence.

## Acceptance

- Contract suites and the experiment register validate mechanically.
- Evidence: [contract tests](../../tests/test_samer_contracts.py), [register tests](../../tests/test_experiment_register.py), and [evidence contracts](CAUSAL_AND_EVIDENCE_CONTRACTS.md).

## Non-goals

- Making a weak benchmark authoritative through procedural consistency alone.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
