# Copy-sort pre-unseal check

The guarded rewriter at `89ac437fa` failed three of 16 same-realm checks. An indexed getter was read twice for both the slice and spread forms. Its second read changed the value in the result. For a sliced Array subclass with a custom `Symbol.species`, the rewrite also changed the constructor of the returned array. The ordinary finite-number, wide Number, sparse, signed-zero, BigInt and mixed-string controls agreed with the original program on these examples.

Run `node check.mjs` beside this file to check the current sibling rewriter. The command exits with status 1 on a difference. It accepts the path to an alternative rewriter for comparison. The [recorded audit](receipt_89ac437fa.json) pins the exact checked source and reports the observed arrays, types and getter counts. This audit used synthetic development fixtures. B3 transfer requires both a passing semantic guard and the existing spent-development coverage gate.
