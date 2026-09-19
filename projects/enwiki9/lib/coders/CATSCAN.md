# CATSCAN: Pure coding implementations

Parent: [enwiki9](../../CATSCAN.md)

## Target

Maintain deterministic coding and inverse implementations with explicit formats.

## Authority

Owns numerical coding semantics, format bounds, deterministic initialization,
and reconstruction. Does not own process control, reporting or scientific decisions.

## Scope

Pure codec implementation modules.

## Contracts

- Input: Explicit bytes, configuration and declared assets.
- Output: Bounded deterministic archives, inverses and scoped witnesses.

## Invariants

- No lab, queue, experiment-results, observer or research imports.
- Required assets and configuration are explicit inputs.
- Distinct interval, rounding and termination conventions remain distinct profiles.

## Acceptance

[Migration tests](../../tests/architecture/test_migration.py) require that the raw-reversal BZip2 extraction produces the original D2REVB01 bytes and
common encoder/decoder reports. Its delivery decodes an invented fixture in a
restricted filesystem containing no experiment results or observer packages.
[Causal-history fixtures](../../tests/test_xml_history_deflate_v1.py) also require
exact byte routing, completed donor availability, paid framing, bounded inverses,
and identical bookkeeping archives for the XML/history diagnostic profile.

## Non-goals

New compression claims, inferred full-state witnesses, or merging unlike coders.

## Freedom

Novel coders may use distinct profiles while preserving declared semantics.
