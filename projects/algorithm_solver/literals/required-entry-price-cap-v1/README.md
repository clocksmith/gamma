# Required owner slots inside priced caps

Item68 combines item61's mandatory owner slots with item63's finite concave
priced prefixes inside one exact allocation. For the same sources, bans, q,
capacity and actual owner count, its charge is no greater than either
predecessor. Budgets below the forced-owner floor remain empty, with null
numerical rows.

The [proof and scope](DRAFT.md), [tiny implementation](proof.py) and
[exhaustive tests](test_proof.py) establish the combination. A coverable tiny
example at its minimum feasible owner budget gives charges20/20/17 and lower
bounds4/4/7 for61/63/68. A zero-valued mandatory slot still consumes capacity.
This uses general supplied q, not reconstructed corpus q53; it is not an
attainment, corpus, M1 or current-best result.

Six focused tests passed0.145seconds; compile/import passed. Root and an
independent reviewer found no blocker; see [review](REVIEW.md). No ancestor
file changed. No private input, scalable kernel, measurement or execution
contract is authorized by this theorem record. Component intent is preserved;
admission, qualification and publication boundaries are unchanged.
