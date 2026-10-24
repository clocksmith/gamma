# Item 57 supplied-input proof: owner path caps

This is a mathematical design with invented exhaustive checks, not a corpus
result. It keeps item 53's nonnegative occurrence penalties and path minimum
fixed, and caps each owner's one-owner penalty contribution by the maximum
weight of a nonoverlapping interval schedule. Shared penalties keep their old
occurrence-sum upper bound.

The [proof](DRAFT.md) shows that capped owner prefixes are discrete concave,
that stable marginal allocation is exact for the numerical relaxation, and
that the resulting lower bound never weakens the old support-class bound.
Top B entry weights per owner suffice for allocation. The interval schedule
must still consider every allowed one-owner occurrence.

The [supplied-input oracle](proof.py) and [tests](test_proof.py) cover strict gains
from cross-entry and repeated-occurrence overlap, unchanged nonoverlap charges,
shared singletons, caps, zero/tied weights, and corruption rejection. Independent
enumeration checks every tiny covering dictionary and encoding path, interval
subset and integer owner allocation. Five focused tests passed in 0.092 seconds;
this is development validation, not a complexity measurement.

No private inputs, multiplier optimization, witness, execution contract or launch.
The explicit oracle materializes the tiny full substring graph and is not a
scalable production implementation. Any later implementation must justify its
full-graph scheduling calculation and receive a separate freeze and review.
