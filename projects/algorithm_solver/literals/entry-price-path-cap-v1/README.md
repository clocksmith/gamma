# Item63: entry-price owner path caps

Proof-only refinement of item57. Charging at most λ per used owner entry leaves a residual interval schedule; taking the minimum of these affine bounds and original activation prefixes preserves concavity and cannot weaken57.

The [derivation](DRAFT.md), [explicit oracle](proof.py) and [exhaustive tiny tests](test_proof.py) use supplied nonnegative integer penalties and a finite integer lambda family containing0. They neither load corpus data nor choose prices.

A constructed coverable k1 example lowers the charge20→17 and raises the integer bound−4→−1. It demonstrates strictness on general fixed q, not positive certification, q53 strictness, optimal prices or corpus gains. Six focused tests passed in0.112 seconds. See the [review record](REVIEW.md).

No scalable implementation, private input, benchmark, binder, pending contract, execution or promotion is authorized. Items60/61/62 remain separate mechanisms.
