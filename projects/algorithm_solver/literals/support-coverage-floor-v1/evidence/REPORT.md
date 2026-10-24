# Item 56 shared-only coverage floor

Every covering dictionary needs at least r one-owner entries on each fixed 300-source cohort. The 256-entry capacity is relaxed for this necessary condition. All 96 paid alphabet singletons are allowed here, so r equals the private-character-source count exactly; independent path replay cannot produce a stronger floor on these inputs.

| Cohort | Coverage floor r | Private-character floor | Coverable by all shared entries | Item50 k* | Positive budgets below r | Positive budgets not ruled out |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| R | 3 | 3 | 297 | 2 | [0, 1, 2] | [] |
| naming | 3 | 3 | 297 | 2 | [0, 1, 2] | [] |

Predictions: {"P1": true, "P2": true}

k<r is coverage-infeasible, before fraction or capacity matters. k>=r is only not ruled out by this floor: it does not prove coverage, a256-entry dictionary, or10% character share. The floor is not a minimum achievable support budget.

Accepted item50 shared-pool completeness; original parser and input hashes; unchanged item50 AC matcher.

Production uses trie occurrences and prefix reachability; replay uses fresh AC occurrences and suffix reachability. Every prefix/suffix recurrence and exact source-success set is checked privately. Public output contains only aggregate counts and hashes.

No q, seed,400-source carrier, validation, cases, source execution or witness packets. Only exact original item13 qualification is reused; item23 unchanged-source exit137 remains separate. No M1, semantic-reuse, fraction sufficiency, current-best or promotion claim.
