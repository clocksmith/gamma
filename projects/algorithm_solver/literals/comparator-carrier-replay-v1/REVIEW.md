# Item 58 review: corrected historical carrier identity

2026-10-24 UTC. This records accepted execution of the separately reviewed
[freeze](FREEZE.md). The active contract SHA256 is
`1f85c00f5e005bc7c47880a305f74aff676743dfab6496f4157267d79788ed31`.
No frozen item 54/51/46/52 file, candidate source, dictionary or result was changed.
No additional run or promotion is authorized by this record.

## Scientific authority and identity correction

Item 54's accepted record `187e06a09` supplies all candidate scientific replay:
12 policy views, exact per-ID rows, qualification, global proposal/ban legality
and 4,800 decoded packet views. Its result SHA256 is
`5fac5a5b4192cf222ccdb502d9005a61d7e7edabb977b3bd25897541e6321e76`.
Item 58 reaggregates those public rows and reconstructs the original predicates;
it does not repeat the candidate search, candidate decoding, proposal replay or
qualification. The historical comparator is fixed item 51 flat, recorded in
`5389ce575`, evidence hash
`c287fe481d1bac9b505c337b5c6fa6cdd875a928ca07e3274d5efcd7808bb77a`.
It is not an automatic pointer to the current best.

The original item 54 adapter compared different JSON carriers. Item 58 binds
them separately and reconciles their ordered contents through the pinned writer
and binary serializer. The seed identity receipt is:

| Identity | SHA256 |
| --- | --- |
| Original item 43N JSON | `f53db5b5944fc0834fbca169a36dfde9577bd320feb8f59d45e77f3c6961a702` |
| Item 54 rewritten JSON | `c957d98f07a79f8d3382ce2fefeeddac425145c465ea2f0f5caaa4ba21872762` |
| Ordered seed binary | `e92315995ea78a76a4d4a2ea33399c2c2349ade5014dce1bfa04d4aadf09dc37` |

The seed has 256 entries, 92 singletons and 2,692 binary dictionary bytes.
The selected item 51 dictionary is a distinct 2,696-byte dictionary, JSON hash
`75ff15afa292eac704a3376ff268194fe15968bedf026433054e510f3bf2c63d`,
binary hash `bb37414caa64e1840dd9309a1cfc63b7263dda550ee2723a9dd0b09af1389afb`.
Actual ordering is preserved; matching sets or aggregate N cannot stand in for
these identity checks.

Exactly four bounded private carriers were authorized: original item 13 source
JSON, original item 43N seed JSON, selected item 51 dictionary JSON and item 51
canonical result JSON. Their byte sizes were 107,350, 2,689, 2,693 and 115,289,
respectively. The hashes and read receipts are in the sanitized result. No
private item 54 artifact, q, cases, observations, other source carrier, recursive
inventory, protected or final-heldout input was read. Source text was parsed,
never executed. Recording itself opened none of those carriers.

## Comparator and gate replay

Original source hashes match item 13 passing qualification and both item 54 U
and item 51 authorities. The actual item 51 ordered dictionary independently
re-encodes all 400 sources under canonical `(N, complete IDs)` and min-C
`(N,C,complete IDs)`, then decodes all 800 packets to exact source bytes.
Canonical per-ID costs, split aggregates, 300 fit nonregression checks and
original canonical character/objective counts reconcile with both public
item 51 evidence and its hash-bound private result. Min-C character counts are
separate; they do not replace canonical counters in the historical authority.

Original full-source/body bans are reconstructed with the unchanged old parser
in 25 batches of 16 inputs. The receipt records 400 parsed variants,
3.986011953 seconds, no execution cache and no persistent parser. The comparator
ban scope remains original sources; spelling variants are not retroactively
added to that historical comparator population. Shared encoder, aggregation,
packet and parser helpers are explicit immutable dependencies.

The validation100 comparator totals are N=8,183 and actions=8,283 under both
policies, with canonical C=4,051 and min-C C=3,991. Their fractions are
0.4950507148967371 and 0.48771844066968106. Raw package size is 14,979 bytes,
or 27,989 including the common decoder inventory. Full fit300 and validation100
coverage and qualification are retained, with a legal 256-entry dictionary.

All three S candidates pass own-control transfer and R readiness under both
policies. Their historical item 51 comparisons fail: 24-S is 53 actions worse,
43N-S is two worse, and 43W-S is 18 worse and also fails median nonincrease.
The paired action counts are respectively 0/79/21, 0/98/2 and 5/74/21
(better/same/worse). Their character fractions improve under both policies, but
the frozen strict-action requirement remains unsatisfied. Complete standing
reference failures and effects are tabulated in the [README](README.md).

R1 and R2 are true, the ranked passing list is empty, and selected_successor is
null. Restated item 54 P1–P4 are true, with P4 meaning no successor. The original
item 54 P4 is explicitly retained as null in `parent54_P4_preserved`; neither
its unresolved report-v2 nor older item 43N report-v1 is overwritten. This
corrective comparison supplies a new historical result, not an altered past
verdict or a current-best/promotion claim. M1 gaps remain byte-for-value equal
to the accepted item 54 metadata.

## Bounded completion and record-only audit

The [supervisor receipt](evidence/supervisor.json) is complete with actual integer
exit 0, no outer timeout, matching contract, and 0.000072587 seconds of completed
cleanup. Whole elapsed time is 4.546927202027291 seconds and worker time is
4.3985081349965185 seconds. Peak worker RSS is 74,380 KiB; installed runtime
size and simultaneous aggregate memory are not claimed. Normal cleanup and
publication fit the original envelope. One absolute emergency budget is retained
for failures, with no reset or automatic retry.

The record audit verified all 194 code and 56 runtime pins unchanged, exact
result/supervisor contract identity, complete/zero-exit/time bounds, public
schema and per-row allowlists, per-ID action/packet/qualification arithmetic,
all aggregate fractions/packages, and all original transfer/standing-reference
tables against accepted item 54. It confirmed R1/R2, all restated predictions,
no successor, preserved parent P4=null, false current-best/promotion flags and
zero fresh jobs/source executions. It did not rerun the experiment or re-open
private inputs. README/REVIEW were checked outside the execution pins.

Only these byte-exact metadata artifacts were copied:

| Artifact | SHA256 |
| --- | --- |
| [results.json](evidence/results.json) | `faf7e095700c1aeb74beb964ece77bc4ec75aa08b75a63c9ad4af94ac386684d` |
| [supervisor.json](evidence/supervisor.json) | `a9ef9b413bbfe2ba75f0a215a951a40b25c314b28882b1fff2f98de2dafd2edf` |
| [REPORT.md](evidence/REPORT.md) | `0c68731bc88b6464918244a3f31c98886add7a09bf1a751e340ad523b7649efb` |

Per-ID hashes/costs and named carrier hashes/paths are permitted metadata; source
code, vocabulary strings, cases and raw errors are absent. New comparator packet
decodes are 800; new candidate decodes are zero, with 4,800 inherited views named
separately. Fresh qualification, source execution, models and training are zero.
Decoder dependencies cost 13,010 bytes; offline implementation source totals
822,842 bytes. Previous item 54 production and both independent-report costs
remain in their original record. Item 46's fit timeout remains unresolved.

Component intent is preserved: explicit historical authority, exact ordered
identity, complete paid costs, retained failures and unchanged acceptance gates.
No new source/algorithm optimization, independent confirmation, M1 admission,
semantic-reuse, current-best update or promotion is asserted.
