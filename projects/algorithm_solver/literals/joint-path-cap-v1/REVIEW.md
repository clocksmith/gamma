# Item60 proof-only review

Reviewed2026-10-23 EDT. Scope: [DRAFT](DRAFT.md), [supplied-input oracle](proof.py) and [exhaustive tests](test_proof.py). No private input, corpus timing, new production kernel, binder or launch was used. The root mathematical/code review and reciprocal independent read-only review found no blocker; the latter did not rerun tests or edit files.

The per-source bound is valid because actual shared penalties are no larger than local top-s all-occurrence weights, actual owner-only penalties are no larger than the owner's top-t weights, and their union is a nonoverlapping subset of all allowed arcs. Capping the sum by Rall therefore bounds actual used q. It does not bound the dictionary's complete activation sum.

For a fixed split, adding S to a concave owner prefix and capping it preserves nonnegative nonincreasing increments. The implementation correctly starts from the generally nonzero sum of capped shared baselines, retains finite zero-valued slots and uses stable owner/rank ties. Thus its marginal allocation is exact for this relaxation. It does not pretend that independently selected shared sets agree across sources.

Both the joint inequality and57's inequality apply to the same actual one-owner count j. Taking their minimum at each j is therefore sound; maximizing those minima over j<=k gives a valid charge and preserves dominance over57. Weak duality with unchanged L,D yields the exact integer ceiling. All scheduling arcs, including entries omitted from top lists, remain in Rall. Bounds remain conditional on fixed source, bans, ownership, capacity and q; a positive value alone does not prove coverage feasibility.

Six focused checks passed in0.114seconds. Independent tiny oracles check every covering dictionary/path, interval schedule and owner allocation, plus18deterministic random pools. The strict fixed53example has a covering witness attaining16 after57's bound−22. The shared-coupling example exercises the necessary minimum with57. Additional cases cover repeated occurrences, shared singleton support, zero/tied weights, capacity0/excess, finite counts, missing/negative/bool penalties, no full-graph path and optimized-Python rejection. Syntax and links were checked; no broad suite or complexity measurement was run.

The prototype materializes explicit substring occurrences and strings, with potentially quadratic occurrences and cubic substring-byte storage. Its test timing is development evidence only. The separately named next-design document introduces no production code or measured result. Gamma intent is preserved: named conditional targets, exact paid entries, reproducible small oracles and no unsupported scientific or promotion claim.

## 2026-10-24: paired implementation and measurement review

Root reviewed production local-weight accumulation/full all-arc forward DP and
independent fresh AC/local full sorting/backward schedule. Their allocation
implementations differ (next-marginal heap versus repeated owner scan) and all
scientific fields agree. Shared33 structural index and inherited57/53 kernels
are declared dependencies, not wholly independent implementations. Every
production57/60 forward recurrence is separately verified by the checker.
Eight production, eight checker and13 tiny lifecycle checks passed; six proof
checks make the measured oracle suite22. Prior accepted output preservation,
absolute cleanup deadlines and blocked failure I/O have focused coverage.

Claude approved the pinned protocol a1fc7c5ed before launch. All49code/12runtime
pins stayed unchanged. The two exact fixed fixtures independently reconcile
all50/53/57/60 curves and historical commitments. Result SHA256:
`3e4a63a79cf6b819d7e1a0bddd5d2696c93bc41b43958bf38b5506fe63bd7bf6`;
supervisor SHA256:
`901eb7849f94a60540519f395d072ffdfb819e527695968abfe1dd49ce89d3a0`.
No original-fit claim follows from this accepted invented observation. Component
intent is preserved; no boundary change or modification of frozen ancestors.

## 2026-10-24: original-fit execution record

Root and independent stable-wrapper audits found no blocker;18 focused checks
passed. Claude approved freeze1bfc35bc6 before activatione1bd83ebd. Exact active
contract1b01460f48b880c4ddd2810cf82fca74a19ea93a7bf9424c12c02e6062105c42.
Both phases completed with zero integer exits and cleanup before publication.
Every109code/23runtime pin was rechecked unchanged. Public result SHA256:
`bda50970d789f8c93d00a9cc5e0dbc6debdf45ea74b3198fc1b91cccf2e2fcbd`.
Every257 raw charge and integer bound equals57 in both original cohorts.
The preserved result is null; no attribution to an untested combined method.
61 is separately shown descriptively, not retrofitted into60 predictions.
Private proof vectors/identities remain private; public artifacts are hashes,
aggregates, numerical curves and receipts. Intent preserved, no boundary change.
