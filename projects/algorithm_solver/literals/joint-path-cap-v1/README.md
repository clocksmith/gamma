# Item 60: joint path caps match the existing original-fit bounds

The independent original-fit replay accepted, with **no raw or integer gain at
any of257 budgets in either cohort** relative to item57. The local shared/all-arc
relaxation is valid but does not strengthen these fixed penalties and sources.
This null result does not establish that every possible joint cap or the later
required-owner combination is ineffective.

| Cohort / method | k3 lower bound | Largest positive k | k256 lower bound |
| --- | ---: | ---: | ---: |
| R,57 frozen comparator | 6651 | 8 | -26872 |
| R,60 joint cap | 6651 | 8 | -26872 |
| R,61 required owners, descriptive | 13349 | 9 | -26872 |
| naming,57 frozen comparator | 119 | 3 | -27652 |
| naming,60 joint cap | 119 | 3 | -27652 |
| naming,61 required owners, descriptive | 6011 | 4 | -27652 |

The61 rows are a descriptive comparison requested during cross-review, outside
60's frozen predictions. P1 passes; P2–P5 are false. Item61 supplies the strongest
recorded exclusions among these methods. All refer to10C-N on the original300
fit sources per cohort, capacity256, frozen allowed full-substring universe,
global whole-source/solve-body bans and paid singletons. k0–2 are coverage-vacuous;
item59 proves the at-most classes from3 upward nonempty. Fullk256 stays negative
and inconclusive. This is no new dictionary, M1 result or current-best change.

The [freeze](FREEZE.md) was pushed1bfc35bc6 and approved by Claude before
activatione1bd83ebd. Production supervisor accepted19.851610seconds and the
independent report91.750261seconds, both exits[0,0], cleanup0.000092/0.000101s.
Worker production peaks549316/527916KiB and report731012/711784KiB (R/naming)
are separate measurements. Aggregate production JSON was55,807,567bytes and
fit the unchanged64MiB read cap. All109code/23runtime/26public pins remained
unchanged. Eighteen focused wrapper checks and root/independent audits preceded
execution; measured kernels retained their earlier oracle checks.

[Full numerical curves](evidence/results.json), [report](evidence/REPORT.md),
[production receipt](evidence/production-supervisor.json) and
[report receipt](evidence/report-supervisor.json) preserve the result.
Both phases freshly rebuilt50/53/57 from exactly the original nine files and
verified every57/60 forward recurrence, independently rebuilt local shared
weights and all-arc backward schedules, and agreed on all allocations/digests.
No private57 output was input; shared structural dependencies are explicit.
No required-owner constraint was applied. No source execution, qualification,
new packet, validation or protected input. Exact13 qualification reuse and23's
unchanged-source exit137 caveat remain. Current best stays51.

## Earlier proof and invented measurement record

# Joint path caps: a proof and tiny exhaustive checks

The [proof](DRAFT.md) gives a valid fixed-q charge on actual path-used penalties that never weakens [item57](../owner-path-cap-v1/DRAFT.md). It caps shared and one-owner contributions together within each source, then takes the minimum with57at each dictionary-slot split before maximizing across allowed splits.

For a fixed shared allowance s, each owner contributes `min(S_p(s)+A_p(t), Rall_p)`. Its value at t=0 can be nonzero. Starting from that baseline, stable largest-marginal allocation exactly solves the stated concave numerical relaxation. Shared choices are independently relaxed across sources; this is not exact global dictionary optimization.

A tiny example at genuine fixed53character potentials uses sources `abc` and `abd`, bans the whole sources and allows B=3entries. At k=2one-owner entries,57's charge76 becomes38, raising the integer lower bound on F=10C−N from−22 to16. Dictionary `{a,bc,bd}` covers both sources and has F=16, so the strict toy improvement is attained in a nonempty class. This is no corpus measurement.

The shared-coupling counterexample matters too: two sources can prefer different shared entries, producing a joint relaxation charge20 when one global shared slot permits charge10. Taking the pointwise minimum with57retains its stronger global shared constraint. Omitting that minimum would lose the dominance guarantee.

[proof.py](proof.py) is an explicit full-substring oracle for tiny supplied strings, not a scalable implementation. [Six focused checks](test_proof.py) passed in0.114seconds. They independently enumerate interval sets, finite owner allocations, dictionaries and every complete path, including18deterministic tiny random pools, repeated occurrences, shared singletons, zero/tied weights, finite entry counts, exact integer ceilings and rejection of invalid inputs. Syntax and draft links were checked. [Independent review](REVIEW.md) found no blocker without rerunning tests.

There are no private inputs, optimized multipliers, source executions, corpus results, feasibility claims beyond the explicit toy witness, M1/default changes or production launch. Existing57/53records remain unchanged. A separate [implementation proposal](DRAFT-NEXT.md) is design only and has no execution authority.

## 2026-10-24: invented implementation measurement accepted

The separate [invented protocol](SYNTHETIC-SPEC.md) at a1fc7c5ed was approved by
Claude before its single measurement. The [result](synthetic-results.json) and
[supervisor receipt](synthetic-supervisor.json) both complete, exit0, under spec
`9f782f67c21128d4c5c0effcf84db6a6c8dc1312027b61a76fff245a89802f7b`.
All49 code/12 runtime pins remained unchanged. The two unchanged50/53/57
fixtures,22 oracles, both kernels, all historical digests/curves, every57/60
forward recurrence, cleanup and publication fit the180-second envelope.

| Invented fixture | Strict raw / integer budgets | Largest positive k,57→60 | k256 bound,57→60 | Production / checker seconds |
| --- | ---: | ---: | ---: | ---: |
| paired_prefix_75k | 0 / 0 | 81→81 | -57362→-57362 | 10.367476 / 60.804791 |
| repeated_one_owner_12k | 256 / 256 | 4→10 | -151368→-13900 | 3.189308 / 4.613335 |

Whole result81.158004seconds; supervisor81.158103seconds; cleanup0.000158seconds.
Worker peak647128KiB, supervisor71036KiB, separate peaks. Oracle time0.638044s.
The checker sorts94003200 source/shared-entry pairs on the first fixture and
checks19737600 concavity increments; these costs are included. No timing ratio
against older protocols or corpus estimate is claimed. The null first fixture
and strict second fixture are both retained; no adaptive resizing or rerun.

These are invented results only. No original-fit input was opened. The separate
[corpus proposal](DRAFT-NEXT.md) still requires its own frozen protocol and
Claude review before activation. Original57 science and all measured files are
unchanged. No M1, new dictionary, qualification or current-best change.
