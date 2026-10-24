# Item 62 proof-only record

2026-10-24. The combined required-owner/joint-path relaxation is valid and
dominates both item 60 and item 61 for every defined k>=r. Below the required
owner floor r, it reports explicit emptiness with null numerical fields.
See [the proof and scope](DRAFT.md) and [review notes](REVIEW.md).

The construction applies mandatory owner slots inside the joint functions,
preserving their nonzero shared baseline. At each fixed j it takes the minimum
with item 61's required-owner/global-shared charge, then maximizes over j>=r.
It exactly solves those finite numerical allocations, without claiming a
globally realizable shared dictionary or jointly attainable path caps.

Six focused checks passed in 0.138 seconds using
`/home/x/deco/gamma/.venv_rocm/bin/python -B -m unittest test_proof` in this
directory. They enumerate tiny covering dictionaries and every encoding path,
interval subsets and required owner allocations. They also cover mandatory
baseline saturation, zeros/ties, bans, capacity edges, malformed inputs and
optimized-Python rejection. This is development correctness evidence, not a
complexity measurement.

A fixed-q toy with five sources and a six-entry covering dictionary gives
charges 76 (60), 104 (61), and 66 (62), with common L=126 and D=1. The respective
integer F lower bounds are 50, 22, and 60. The witness has F=88; it establishes
feasibility at k=4 but does not attain the bound. Strict gain against both
components occurs here, not universally.

Only [proof.py](proof.py) and [test_proof.py](test_proof.py) execute, using supplied
tiny inputs and unchanged mathematical 60/61 oracles. No private data, corpus
design, production kernel, pins, binder, benchmark, run or promotion was made.
Existing Gamma intent, historical evidence and milestone gates remain unchanged.

## 2026-10-24: supplied allocation and continuation design

The new [pure allocator](allocation.py) has heap and owner-scan methods and
[focused tests](test_allocation.py). Six checks passed, including the exhaustive
proof oracle,24 tiny random graphs at four capacities,257 rows, clipping,
mandatory saturation, finite zero ties, negative L and malformed inputs. Root
and independent read-only review found no blocker. Shared validation/formula
and row construction are explicit; the two marginal traversals differ.
No source ownership, shared identities or reachability is established by this
supplied-prefix API; their provenance must come from separate authority.

Separate60/61 records now exist:60 is null against57, while61 strengthens the
small support budgets. The [continuation design](DRAFT-NEXT.md) inherits accepted
60 graph receipts and freshly reconstructs forced owners and the combined
allocation. It is an implementation proposal, not a private-input or launch
contract; a separate reviewed FREEZE remains necessary.
