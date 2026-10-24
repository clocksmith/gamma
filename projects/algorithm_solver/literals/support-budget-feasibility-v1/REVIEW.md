# Item 59 review: a public-lineage coverage witness

2026-10-24 UTC. Root and a separate agent verified the public-record inference.
Claude mathematical review has been requested; this draft does not claim that
approval. No new execution or corpus authority is granted.

The named proof target is minimum one-owner support budget for coverage of the
original R/naming 300 fit sources, subject to at most 256 paid entries and the
same global source/body bans. It is distinct from the fraction target, canonical
action cost, semantic reuse, M1, or a protected-population result.

## Lower bound and matching upper bound

Accepted item 56 gives the lower bound three, even when all shared entries are
allowed and dictionary capacity is relaxed. Thus the bound also holds with the
256-entry cap. It is not an achievability argument by itself.

The upper bound uses accepted item 13 control/scope_joint width-8 dictionaries.
Both contain 256 entries, have 300 encodable fit rows with packet digests, report
300/300 fit coverage and qualification, and have no illegal-entry hashes. Their
exact dictionary SHA256 values are:

* R: `aecd214632368bd53c2d784c09b0830186b0da3f3341427725b820b2484b7836`.
* Naming: `e3cb3e3cb4017596ca8b8103a39ec5747198a00e143c739ef28393f4215d0c38`.

These equal the item 50 seed pins. Item 50 checks unique seeds of at most 256
entries, exact source hashes, empty seed/pool intersection with regenerated
bans, and seed inclusion in the pool. Its independent checker repeats seed
membership and ban checks. Item 56 independently classifies every occurrence
and finds exactly three one-owner entries in each of those pools. Consequently
each existing covering seed has at most three one-owner entries. Combining this
with the lower bound proves both seeds have exactly three, and the optimum
support budget is exactly three under the cap.

No assumption that one private character per source generally restores coverage
is used. No assumption about seed entries being useful or occurring is needed:
absent entries still consume dictionary capacity but are not one-owner entries.
The dictionary as recorded already covers every source. The inference uses
at-most support budgets, so the same witness applies to every k>=3 through 256.

## Exact public identity and inherited evidence

The audit compared all 300 fit IDs and per-source SHA256 values from item 13
against item 50's contract. It reconciled source identity/file hashes, bans,
pool hashes/counts and occurrence-order hashes across items 50 and 56. The
original item 13 evidence hash matches item 50's public pin, and each report's
contract hash matches its actual public contract. Item 53's accepted positive
budgets were checked to be exactly 0,1,2, matching item 50.

The inspected item 13 reporter, [report.py](../binding-descent-v1/report.py),
lines 23–35, hashes the dictionary and chosen source, reconstructs the shortest
encoding, asserts exact packet decoding, and records each packet digest. Its
public evidence has those digests and encodable flags for all matching fit rows.
This audit consumes that accepted historical decoding evidence; it does not
rerun decoding or independently inspect historical private packets.

The original item 13 reporter was outside its execution pins. Its current hash
is therefore recorded as inspected reporting code, not retroactively described
as frozen execution evidence. The [lineage artifact](evidence/public-lineage.json)
discloses that distinction. The original run.py pin and accepted evidence hash
are checked. Item 50's pinned [binding.py](../potential-lift-certificate-v1/binding.py)
lines 178–191 and [independent.py](../potential-lift-certificate-v1/independent.py)
lines 128–138 supply the seed/source/ban/pool membership authority. Root and
agent audits found no remaining identity or scope gap in this inference.

The artifact hashes 15 public files and checks 16 existing contract-to-file pin
links. It retains only aggregate counts and hashes, no private relative input
paths, source text, source IDs, vocabulary entries, q, potentials or case data.
Its SHA256 is
`1a126e65656a228110c763900a2981718d9806fa04b7dc46229e19f88a6d5342`.
No private input was opened, and no qualification, source execution, multiplier
calculation or packet decode was performed for item 59.

## Consequences and limits

All positive item 50/53 fraction bounds remain in empty covering classes k<3,
so the dated item 56 vacuity finding is unchanged. The new cross-record witness
resolves coverage at and above three. It does not resolve whether any of those
nonempty classes achieves C/N<=10%, and their nonpositive fraction bounds remain
inconclusive. Existing seed fit fractions are 0.5406388846330626 for R and
0.4981010101010101 for naming; those witnesses do not meet the target.

Qualification remains the exact original item 13 source record, with item 23's
later unchanged-source exit 137 retained as a separate limitation. This is no
fresh behavioral confirmation. No minimum dictionary size, canonical optimum,
M1, semantic-reuse, unseen-family, publication-readiness or global dual-optimum
claim is established. The dated cross-references preserve the earlier floor-
only statements as historical scope and supply this later evidence separately.
Component intent, admission thresholds, protected populations and owner gates
remain unchanged.

## Dated cross-review: 2026-10-24T02:38Z

Claude independently confirmed the seed-subset, coverage and three-entry-floor
argument through the team log, including minimum feasible k=3 and the absence
of a nonvacuous10% exclusion in these full-substring support classes. The
public-lineage artifact retains its pre-review status and original hash; this
prose records the later review without rewriting that audit snapshot.
