# ACS-PROVER Theorem Library

Status: pre-specification constructive manuscript
Version: `ACS-PROVER-LIBRARY-1`

This is not a precommitted examination and creates no solver-pass claim.

The corresponding formal independent problem bank is
`docs/acs_prover_problem_set.md`. Its provenance explicitly states that the
constructive manuscripts predate the formal specification.

## Canonical status

```text
mathematical status: COMPLETE
prover transfer: NOT YET INSTANTIATED
candidate affected: false
Hutter score credit: 0 bytes
```

Problem B assumes a fixed total order on vertex identifiers.

## Modules

| Module | Guaranteed result | Boundary |
|---|---|---|
| A | Exact optimum in a supplied bounded-treewidth factorization | Does not prove the family contains a competitive compressor |
| B | Canonical rank/unrank and optimal injective fixed-length ambiguity tag | Does not prove net transform savings |
| C | Exact finite-state final-state and modeled-cost recomposition | Does not prove emitted-byte identity or practical state enumeration |
| D | Exact minimum peak in the atomic tree, no-recomputation model | Does not prove actual RSS |

## Problem C pilot contract

The first live instance is a five-state XML lexical transducer. Its state,
transition, vector cost, finalization, block size, and replacement operations
are frozen in `tools/acs_prover_weighted_monoid.py`.

Transfer requires:

1. Enumeration of every state.
2. Exact block summaries for every initial state.
3. Exact balanced-tree composition.
4. Point and fixed-length interval replacement.
5. Equality with full replay for final state and every cost coordinate.
6. A receipt identifying the input and implementation.

Passing changes only the Problem C prover-transfer status for this frozen
instance. It does not affect a candidate or receive compression credit.

## Live transfer: XML lexical transducer

Status: `PROVER_TRANSFERRED` for
`results/acs_prover_c_xml_lexer_v1/receipt.json`.

The exact summary tree matched full replay from all five enumerated states for
the base stream, one point replacement, and one fixed-length interval
replacement. This changes neither `candidate affected: false` nor
`Hutter score credit: 0`. The separate compression-derived endpoint experiment
is terminal negative at
`results/acs_prover_xml_state_endpoint_shadow_v1/decision.json` and does not
weaken the theorem-module result.
