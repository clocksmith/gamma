# Joint path caps: a proof and tiny exhaustive checks

The [proof](DRAFT.md) gives a valid fixed-q charge on actual path-used penalties that never weakens [item57](../owner-path-cap-v1/DRAFT.md). It caps shared and one-owner contributions together within each source, then takes the minimum with57at each dictionary-slot split before maximizing across allowed splits.

For a fixed shared allowance s, each owner contributes `min(S_p(s)+A_p(t), Rall_p)`. Its value at t=0 can be nonzero. Starting from that baseline, stable largest-marginal allocation exactly solves the stated concave numerical relaxation. Shared choices are independently relaxed across sources; this is not exact global dictionary optimization.

A tiny example at genuine fixed53character potentials uses sources `abc` and `abd`, bans the whole sources and allows B=3entries. At k=2one-owner entries,57's charge76 becomes38, raising the integer lower bound on F=10C−N from−22 to16. Dictionary `{a,bc,bd}` covers both sources and has F=16, so the strict toy improvement is attained in a nonempty class. This is no corpus measurement.

The shared-coupling counterexample matters too: two sources can prefer different shared entries, producing a joint relaxation charge20 when one global shared slot permits charge10. Taking the pointwise minimum with57retains its stronger global shared constraint. Omitting that minimum would lose the dominance guarantee.

[proof.py](proof.py) is an explicit full-substring oracle for tiny supplied strings, not a scalable implementation. [Six focused checks](test_proof.py) passed in0.114seconds. They independently enumerate interval sets, finite owner allocations, dictionaries and every complete path, including18deterministic tiny random pools, repeated occurrences, shared singletons, zero/tied weights, finite entry counts, exact integer ceilings and rejection of invalid inputs. Syntax and draft links were checked. [Independent review](REVIEW.md) found no blocker without rerunning tests.

There are no private inputs, optimized multipliers, source executions, corpus results, feasibility claims beyond the explicit toy witness, M1/default changes or production launch. Existing57/53records remain unchanged. A separate [implementation proposal](DRAFT-NEXT.md) is design only and has no execution authority.
