# Global entry pricing: theorem record

Item 66 proves a cardinality-aware charge across all fixed source paths.
For each allowed entry, divide a nonnegative integer price by its total
occurrence count across all sources, rounding down. Subtract that amount
from each occurrence penalty, clipping at zero. Each selected entry removes
at most one price globally, so a dictionary with at most B entries has
penalty at most `lambda*B + sum(residual path caps)`.

The [proof and scope](DRAFT.md), [tiny oracle](proof.py) and
[exhaustive checks](test_proof.py) keep source geometry, bans and paid entries
fixed. An explicit minimum with the same-q item57 charge preserves its bounds.
Zero price alone does not recover or universally dominate item57 or item63.

A coverable invented example gives charges 80 for item57, 60 for item60 and
52 at a positive global price. Its lower bound remains -58. Another example
attains a positive bound, but both use supplied general q, not corpus q53.
Neither establishes original-fit improvement or a full256 certificate.

Seven focused tests passed in 0.126 seconds; compile/import passed. Root and
an independent reviewer found no mathematical implementation blocker; see
[review](REVIEW.md). This is a theorem and tiny implementation record only.
No private inputs, scalable implementation, price tuning or measurement.
A separate reviewed scalable design and frozen protocol must precede either
an invented performance measurement or original-input execution. Component
intent and admission, qualification and publication boundaries are unchanged.
