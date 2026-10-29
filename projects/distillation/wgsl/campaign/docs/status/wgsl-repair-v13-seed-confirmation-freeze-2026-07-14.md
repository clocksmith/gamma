# WGSL Repair V13 Blind Seed-Confirmation Freeze

V13 now has a pre-evaluation protocol for materializing a disjoint semantic
seed-confirmation population. No confirmation task has been materialized and
seed 29 has not received a confirmation prompt at this stage.

The commit containing this document, the materialization policy, the generator,
the 12-blueprint catalog, and the CPU-oracle implementation supplies the
population entropy. The generator ranks blueprint identifiers within frozen
arity and parameterization strata using domain-separated SHA-256 values derived
from that full commit hash. It selects four unary and four binary tasks, split
equally between parameterized and non-parameterized tasks, then independently
derives parameter choices, input seeds, and shape variants.

The protocol requires this order:

1. Commit and push the policy, generator, catalog, and oracle implementation.
2. Materialize the population from that exact commit.
3. Commit and push every generated source, its manifest, and the candidate
   evaluation policy.
4. Qualify every reference shader through Chromium WebGPU dispatch and the CPU
   oracle.
5. Run selected external20 seed 29 exactly once.

The generator verifies that the freeze commit contains byte-identical copies of
all bound inputs and is an ancestor of the executing checkout. The generated
manifest records the freeze commit, every selection digest, the selected
blueprint identifiers, source hashes, and the no-prior-inference assertion.

This process can confirm or reject seed 29 on replacement-only semantic repair.
It has no promotion, WGSL Doctor, or complete-shader-writing authority. A WGSL
writer remains a separate experiment with specification-to-complete-shader
inputs and its own compilation, dispatch, CPU-oracle, bounds, metamorphic, and
promotion populations.

The original unstratified V1 materialization was invalidated before reference
qualification or candidate inference because its blind subset happened to
contain seven unary and six parameterized tasks. Its immutable invalidation
receipt is
`wgsl-repair-v13-seed-confirmation-materialization-v1-invalid-2026-07-14.json`.
