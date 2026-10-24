# Item 56 review: coverage floor and vacuity of the positive support band

2026-10-24 UTC. The [freeze](FREEZE.md) was pushed as `dde1d7485`, reviewed by
Claude, and activated exactly in `a67bbbae6`. The active contract SHA256 is
`3c24fece157016e80afeb6b341d44614a09c843f03e71a57f96e290ae67a10c3`.
This record authorizes no further run and changes no frozen execution file.

The theorem is a necessary coverage condition: give every source access to all
allowed shared entries at once. Each source still not coverable requires at
least one one-owner entry, and such an entry serves only its own source. This
relaxes dictionary capacity. The accepted source alphabet and no-banned-pool
conditions additionally imply that this count equals the number of sources
containing a private character. That equality was registered before input
access and checked during execution and replay.

The original general banned-singleton test remains valid outside this accepted
population. It is not evidence of a stronger floor here. Neither equality nor
the count of private characters proves sufficiency under the 256-entry cap.
No free fallback or uncharged character is introduced by the theorem.

Production reconstructs occurrences with a trie and checks forward reachability.
Independent replay uses fresh AC occurrences, distinct-owner sets and backward
reachability; another AC pass checks every intermediate prefix and suffix
recurrence. The reporter compares source-success sets, owner classes, shared
entry identities, forced/private-character sets, occurrence order and counts.
It verifies private proof commitments again at combination. Only allowlisted
aggregate counts and hashes enter public evidence.

Shared authorities are explicit: accepted item 50 full-substring/shared-pool
completeness, the original parser and exact source/pool hashes, and item 50's AC
matcher. This is independent scalar/ownership/path replay, not an independent
suffix-array or JavaScript-parser implementation. Global full-source and solve-
body bans are regenerated, including primitive bodies, and reconciled exactly.

Focused development evidence comprised six kernel tests, eight execution/replay
tests and nine supervisor tests. Checks include exhaustive tiny coverage,
optimized-Python rejection, the exact two-file-per-cohort loader, corruption of
input/proof/public fields, failed-production refusal before private input,
every-position recurrence checks, a full invented two-cohort pipeline, real
worker/child/grandchild process-group cleanup, and expired failure-publication
budgets. These tests establish only their named behaviors, not corpus results.

Production and reporting each had a separate 1,200-second whole phase and
600-second cohort caps, cores 6/7, 8 GiB address-space limits per process, and one
absolute emergency cleanup/publication allowance of at most 10 seconds. Setup,
imports, hashing, parser children, replay, serialization, normal cleanup and
publication were charged. The accepted [production receipt](evidence/production-supervisor.json)
and [report receipt](evidence/supervisor.json) both show complete status, actual
integer exits [0,0], and completed cleanup. Their elapsed times are respectively
4.094459320942406 and 6.868958005972672 seconds. Result assembly times
4.062837881967425 and 6.362789991952013 seconds precede those completed receipts.

R/naming production worker times were 3.854567398/3.485788922 seconds; report
worker times were 6.266476864/5.696121651 seconds. Production peak RSS values
were 269,680/259,380 KiB and report peaks 428,540/411,712 KiB. These are worker
measurements, not summed simultaneous memory use or a runtime prediction.

## Accepted scientific result and interpretation

Both cohorts have r=3, three private-character sources, three distinct private
characters, and 297 shared-only-coverable sources. Original pool sizes are
308,304/291,196; shared counts 308,294/291,186 include shared singletons. Each
pool contains three one-owner entries and seven absent entries. Replay checks
1,370,583/1,319,319 occurrences over 76,107/76,033 source characters. Full entry
identities and per-source vectors are not published.

P1 and P2 are true. Every positive item 50 budget, k=0,1,2, lies below r; the
remaining-positive list is empty. Accepted item 53 retains exactly the same
positive budgets. Thus **all positive fraction exclusions from items 50 and 53
are vacuous for covering dictionaries on these fixed cohorts**. Their algebra
and numerical curves remain valid; coverage already makes those classes empty.
No conclusion about a nonempty feasible representation class follows from those
positive values. Dated cross-references update the unpinned item 50/53 records
without rewriting their frozen evidence.

For k>=3, coverage is merely not ruled out by this floor. The negative fraction
bounds there do not settle existence, 256-entry feasibility, or C/N<=10%.
This finding does not refute other multipliers, potentials or path-aware charge
bounds. No minimum achievable support, dictionary, packet, global optimum,
semantic-reuse, M1, current-best change or promotion is established.

## Record-only audit and metadata

The recording audit opened finalized public-ready report metadata, both
supervisor receipts, public parent records and public contracts. It did not open
private cohort artifacts, source text, q, pools, per-source flags or cases.
All 43 code and 20 runtime pins matched. The six README/REVIEW recording files
are outside the item 50/53/56 execution pins; no pinned file was changed.

Only four finalized metadata artifacts were copied:

| Artifact | SHA256 |
| --- | --- |
| [results.json](evidence/results.json) | `67e9b08b7ad4515a9dce64624c3bc84c57911fb1a90ceb0899b54a66f08fb12d` |
| [REPORT.md](evidence/REPORT.md) | `7f7e60d7b8b04eba9d0e16c7b62b63398aae4d561f9ca465cf797b0dafadb676` |
| [supervisor.json](evidence/supervisor.json) | `db0c615f57c7c150804c07deadcedd345d1ac6a2ea8843bad1a29ea9be6fad1e` |
| [production-supervisor.json](evidence/production-supervisor.json) | `f9f0e18f8f031a5f63bb3d2a7086b2438dd50c076d227ecc73e567f0fd7ea778` |

Result schemas, allowlisted arm fields, parent source/ban/occurrence commitments,
capacity-relaxed count arithmetic, equality of forced/private-character set
commitments, all positive-budget classifications, timing bounds, exit types and
false promotion/feasibility flags were checked. This was a metadata audit, not
another independent corpus replay or rerun.

Original item 13 exact-source qualification is the only reused behavioral
evidence. Fresh qualification jobs, multiplier searches and witness packets are
all zero; no q, seed, validation, cases or 400-source carrier were read by this
experiment. Item 23's later unchanged-source exit 137 is preserved. Component
intent, owner gates, population boundaries and admission thresholds are unchanged.

## 2026-10-24 later cross-record coverage witness: minimum budget exactly three

[Item 59's public-lineage audit](../support-budget-feasibility-v1/README.md)
combines the item 56 lower bound with the existing exact-hash item 13 covering
seeds. Item 50 verifies those 256-entry seeds are subsets of the same old pools;
item 56 finds only three one-owner pool entries. Each seed thus uses at most
three, while the floor forces at least three. **The minimum feasible one-owner
budget under capacity 256 is exactly three**, and the same seeds witness every
at-most-k covering class for k>=3.

This resolves coverage using additional cross-record witness evidence; the
item 56 floor alone still proves only necessity. Earlier floor-only uncertainty
statements are superseded by this later inference. The vacuity at k=0,1,2 is
unchanged. C/N<=10% remains unresolved in the now-known nonempty classes k>=3;
the existing witnesses do not achieve that fraction. No new private read,
packet decode, source execution or qualification was performed.
