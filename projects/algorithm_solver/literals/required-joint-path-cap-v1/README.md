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

## 2026-10-24: frozen original-fit attempt incomplete

The reviewed [freeze](FREEZE.md) at b2b5fefba and activation422f3db11 ran with contractc51cfb29340a6564f03e7bda0d867eb07d52c3c0a68f346b7dee119590921aef. Production completed in5.022128 supervisor seconds, but the independent report failed its production-receipt guard before ancestral reads. The report supervisor recorded0.349214seconds, exit codes[-9,1], and0.007262seconds cleanup. All167code/23runtime pins remained unchanged.

**There is no accepted62 numerical result.** All predictions are null. The [failure record](evidence/results.json), [report](evidence/REPORT.md), [production supervisor](evidence/production-supervisor.json), [report supervisor](evidence/report-supervisor.json) and [failure receipt](evidence/failure.json) preserve the attempt. Result hash7b9bc87f76202c3dcdda8403e0abcc3852e0d3c90b5ff8cbbcd6d6387fb24664.

The allocator hashes two budget-prefix dictionaries with integer keys. JSON transport converts those keys to strings, so sorting them for replay changes order once budgets reach two digits. The reader correctly rejects the mismatch. A12-slot invented reproduction confirms that only these two digests change; heap/scan mathematical outputs agree. Earlier tiny wrapper fixtures did not exercise actual multi-digit dictionary hashes. This is a serialization correctness bug, not a numerical verdict or license to ignore the digests.

Preserve every frozen file and failed output. A separately reviewed v2 protocol must normalize JSON keys before digest creation and test a real allocation through serialization before any new run. Candidate51 and the61 support exclusions remain unchanged. No packets, qualification, validation, M1 or publication boundary changed.
