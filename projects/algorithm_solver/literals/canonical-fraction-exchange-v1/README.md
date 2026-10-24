# Capped canonical exchange improves fraction without seed regressions

[Freeze](FREEZE.md), [record review](REVIEW.md),
[independently replayed metadata](evidence/results.json).

Both fixed300 fit cohorts improve canonical character fraction after nine
accepted moves, with fewer selections and no per-program selection regression
against the seed. R falls from14115/26108 to13437/25844 character selections;
naming falls from12328/24750 to11691/24496. Neither approaches the ten-percent
target. This is a fixed-fit representation result, not validation, M1 readiness
or replacement of the standing best.

The unchanged item40 pools contain2004 R and1779 naming entries. Every seed has
249 paid entries, every final dictionary256. Characters fall from89 to87; removed
characters have no implicit fallback. Source identities and complete-source/body
bans remain fixed. The canonical policy minimizes `(N, complete ID sequence)`
using sorted dictionary IDs, without a character tie break. These are the same
sorted-seed policy metrics as44's shadow, not historical original-order ties.
N excludes Finish; actions add one per source.

## Seed and final costs

| Cohort / dictionary | C | N | Actions | C/N | F=10C−N | Median / p90 / p95 N | Dictionary bytes | Raw / decoder-inclusive package |
|---|---:|---:|---:|---:|---:|---|---:|---|
| R / seed | 14,115 | 26,108 | 26,408 | 54.0639% | 115,042 | 68 / 162 / 188 | 2,172 | 40,580 / 53,590 |
| R / final | 13,437 | 25,844 | 26,144 | 51.9927% | 108,526 | 67 / 162 / 182 | 2,216 | 40,360 / 53,370 |
| naming / seed | 12,328 | 24,750 | 25,050 | 49.8101% | 98,530 | 64 / 150 / 176 | 2,185 | 39,235 / 52,245 |
| naming / final | 11,691 | 24,496 | 24,796 | 47.7262% | 92,414 | 63.5 / 149 / 176 | 2,229 | 39,025 / 52,035 |

Action median/p90/p95 are respectively one greater than every displayed selection
quantile: final R68/163/183, naming64.5/150/177. R saves264 selections and678
characters; naming saves254 and637. Character share drops2.0712 and2.0839 percentage
points. Final per-source selections improve/tie/worsen versus seed in130/170/0 R
and131/169/0 naming programs. Full package changes are−220/−210 bytes.

All retained states obey each source's immutable seed N cap. The protocol allows
an adjacent increase while staying under that cap, but none occurred in this run.
The following counts compare each accepted state with its immediate predecessor;
all intermediate seed-relative counts and hashes remain in the metadata.

| Move | R better / same / worse | R ΔN / ΔC / Δpackage | naming better / same / worse | naming ΔN / ΔC / Δpackage |
|---|---|---|---|---|
| 1 | 16 / 284 / 0 | −16 / −76 / −10 | 14 / 286 / 0 | −14 / −74 / −8 |
| 2 | 32 / 268 / 0 | −39 / −81 / −33 | 31 / 269 / 0 | −40 / −80 / −34 |
| 3 | 17 / 283 / 0 | −21 / −79 / −15 | 31 / 269 / 0 | −38 / −76 / −32 |
| 4 | 0 / 300 / 0 | 0 / −60 / +6 | 14 / 286 / 0 | −38 / −76 / −32 |
| 5 | 27 / 273 / 0 | −39 / −78 / −33 | 0 / 300 / 0 | 0 / −56 / +6 |
| 6 | 15 / 285 / 0 | −39 / −79 / −33 | 10 / 290 / 0 | −19 / −65 / −13 |
| 7 | 29 / 271 / 0 | −41 / −78 / −35 | 23 / 277 / 0 | −36 / −72 / −30 |
| 8 | 31 / 269 / 0 | −38 / −76 / −37 | 25 / 275 / 0 | −35 / −70 / −34 |
| 9 | 23 / 277 / 0 | −31 / −71 / −30 | 28 / 272 / 0 | −34 / −68 / −33 |

Every accepted move strictly reduces C/N. Two moves preserve every source's N
while reducing C and adding six package bytes; this follows the frozen ratio-first
objective. There were no equal-ratio accepted plateaus.

## Comparison with item44

These use identical fixed sources and sorted dictionary policy, but different
search objectives and acceptance constraints. The canonical rows are the matched
path-policy comparison; min-F rows are separately labeled historical context.

| Cohort / final dictionary / path policy | C | N | C/N | F |
|---|---:|---:|---:|---:|
| R / item44 / min_F | 12,167 | 28,384 | 42.8657% | 93,286 |
| R / item44 / canonical_min_N | 13,026 | 27,240 | 47.8194% | 103,020 |
| R / item47 / canonical_min_N | 13,437 | 25,844 | 51.9927% | 108,526 |
| naming / item44 / min_F | 10,628 | 27,448 | 38.7205% | 78,832 |
| naming / item44 / canonical_min_N | 11,365 | 25,917 | 43.8515% | 87,733 |
| naming / item47 / canonical_min_N | 11,691 | 24,496 | 47.7262% | 92,414 |

Item47's final dictionaries save1396 R and1421 naming canonical selections versus
item44's final dictionaries, while using411/326 more singleton selections.
Item44 achieves lower character share, but its canonical selection totals exceed
its own seed. Item47 answers the narrower question of whether some fraction gain
is possible under per-program canonical seed caps. It does not dominate item44
on every metric or identify an optimal tradeoff.

## Search budgets and verification

Each cohort completes seven free-slot additions, two accepted exchange epochs,
and a third epoch with no improving evaluated neighbor:16 completed sweeps and
nine accepted moves. Both stop with `no_improving_evaluated_neighbor`. Every
declared sweep completed, but swaps use only the top-four addition shortlist;
unexamined swaps and larger moves remain. This is **not** a local or global
optimality result. Other rejected feasible scores remain search diagnostics.

| Cohort | Attempted / completed | Add / rank / remove / swap / full rescore | Coverage failures remove / swap | Cap failures remove / swap | Search seconds |
|---|---|---|---|---|---:|
| R | 21,429 / 21,429 | 12,264 / 5,244 / 768 / 3,072 / 81 | 264 / 1,056 | 477 / 1,908 | 88.702 |
| naming | 19,146 / 19,146 | 10,689 / 4,569 / 768 / 3,072 / 48 | 264 / 1,056 | 477 / 1,908 | 91.576 |

Declared opportunities are21348/19098; counted full rescores account for the
remaining81/48 probes. There are no partial sweeps, omitted declared opportunities,
interrupted probes, partial-sweep acceptances, soft deadline overruns or retries.
Each cohort remained within600 search seconds and50000 evaluations; initial
construction and final artifacts are covered by the separate1200-second whole-phase
limit. Temporary257-entry states are ranking surrogates, never retained packets.

Independent replay rebuilds the parent certificate/pool/bans and independently
canonical-encodes and decodes all20 retained states, including both seeds:
6000 packet views. It checks the trace's enumeration, shortlist and counters,
rescore-before-retention, admission, original source hashes and seed caps. It
rechecks the recorded failed source for every coverage rejection, and one exact
violating source for each cap rejection. That is sufficient to prove rejection;
the extra search-side cap-violation count is not an independently replayed full
failure census. No optimization was rerun during reporting.

P1 (complete covering states respecting caps) and P2 (strict fraction reduction
in both cohorts) pass. P3 (any retained ten-percent fraction) fails. Historical
unrestricted F lower bounds−27266/−28259 remain separate; they are not a canonical
ratio optimality gap or a new impossibility result.

## Scope, reuse and charges

Both seeds and finals have three one-owner entries:3/249=1.2048% versus
3/256=1.171875%. Every paid entry, including unused entries and singletons, is
in the denominator. No seed/final entry covers at least90% of a containing
source; the one-owner-and-near-whole intersection is also zero. Seeds have two
unused entries each; finals have none. These substring-support and size statistics
are descriptive, not a semantic-reuse audit or an eligibility decision.

Packets charge eight bits per selection, zero padding, and41 framing bytes per
source (12300 per cohort); each full package pays its dictionary once plus the
13010-byte decoder inventory. Source sizes76107/76033 bytes are separately
reported. Offline encoder code is1094146 bytes; models/training are zero, and
installed runtime size is unmeasured.

Production completed in98.289 seconds and independent reporting in53.345 seconds
(report supervisor53.368). Both phases used cores4–5,8GiB per worker and separate
1200-second deadlines with bounded ten-second cleanup. Production peak RSS was
547232/546464 KiB; report peak RSS534020/525748 KiB. All166 frozen code pins and
10 runtime pins remain unchanged.

Exact item13 source-hash qualification receipts are reused, with no new source
execution. Item23's retained unchanged-source failure is not repaired. No
validation, protected or final-heldout population was opened. The consumed fit
population gives no independent-confirmation or400/500 M1 claim, and no candidate
is promoted. Component intent and all existing acceptance gates are preserved.
