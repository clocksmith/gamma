# Spelling changes lower the character fraction, but atomic fit search makes no move

[Freeze](FREEZE.md), [design](DRAFT.md), [concurrent-best amendment](AMENDMENT-1.md),
[review](REVIEW.md), [independently replayed metadata](evidence/results.json).

All 4,000 packets decode and qualify, but **J fails the frozen successor verdict**
under both policies. Every fit arm retains the D10 seed. On consumed validation,
S, A and J make the same 21 spelling changes: character selections fall by 82,
while actions remain 8,324. J therefore fails strict action improvement against
D10, D, S and A. No alternative arm is substituted, and current best is unchanged.

The fixed population is 300 fit plus 100 consumed validation programs. D10 is the
item 30 dictionary; D is dictionary-only, S spelling-only, A admits the moves
separately, and J additionally offers atomic source/paid-entry transactions.
Primary segmentation minimizes selections, then character selections, then the
complete ID sequence. Canonical minimum-selection segmentation is a full shadow.
Actions include one Finish per program; N counts selections without Finish.

## Complete paired views

All five arms have 256 paid entries, including the same 92 character entries.
All dictionaries have identical hashes and zero illegal entries. Every row covers
and qualifies its entire split. All fit rows are identical to D10: 24,254 actions,
23,954 selections, action median 64.5, p90 141 and p95 177. Fit character counts are
11,658 (48.6683%) under the primary policy and 11,848 (49.4615%) canonically.

| Arm | Validation actions | Primary C | Primary C/N | Canonical C | Canonical C/N | Changed validation sources |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D10 | 8,324 | 4,047 | 49.2096% | 4,109 | 49.9635% | 0 |
| D | 8,324 | 4,047 | 49.2096% | 4,109 | 49.9635% | 0 |
| S | 8,324 | 3,965 | 48.2125% | 4,027 | 48.9664% | 21 |
| A | 8,324 | 3,965 | 48.2125% | 4,027 | 48.9664% | 21 |
| J | 8,324 | 3,965 | 48.2125% | 4,027 | 48.9664% | 21 |

Every validation view has 8,224 selections, action median 62.5, p90 155 and p95
175 (selection median 61.5, p90 154 and p95 174). S/A/J have identical per-program
source hashes, packet metrics and qualifications. The 21 changed eligible bindings
use six-byte names, replacing one-byte names at 82 occurrences. This increases
validation source bytes from 25,760 to 26,170 (+410), while reducing the character
fraction by 0.9971 percentage points with no action gain. This is spelling-based
character-code reclassification using the unchanged dictionary, not evidence of
an accepted atomic transaction or a necessary paid-entry bundle.

## Search and bounded interpretation

| Arm | Full evaluations | Source trials | Dictionary trials | Context-dictionary trials | Joint trials | Removal probes | Rejected coverage failures | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D | 2,781 | 0 | 384 | 2,232 | 0 | 164 | 3 | 129.681 |
| S | 177 | 176 | 0 | 0 | 0 | 0 | 0 | 53.673 |
| A | 2,957 | 176 | 384 | 2,232 | 0 | 164 | 3 | 116.337 |
| J | 6,989 | 176 | 384 | 2,232 | 4,032 | 164 | 3 | 264.329 |

The full-evaluation total includes the initial incumbent. All four stop with
`bounded_neighborhood_no_improvement`, zero accepted fit moves and zero budget
overrun, below 10,000 evaluations and the 600-second soft limit. These are bounded
menu outcomes, not timeout failures or exhaustive optima. The frozen neighborhood
limits names, top 16 contexts, 192 groups, at most two added entries and 12 deletion
combinations. It does not test arbitrary renamings, larger bundles or longer
sequences of non-improving moves. Rejected fit scores are retained search evidence;
the independent report does not rerun that optimization.

Validation is a separate, predeclared per-source application of sealed fit names
and contexts with a fixed dictionary. It can accept a local spelling change even
when no fit group improved the aggregate fit objective. S/A/J each evaluate 15,008
validation proposals and accept 21 moves; D evaluates none. Thus zero fit moves
and changed validation sources are consistent with the protocol. Every validation
proposal is independently rescored. The validation choices use consumed inputs;
they do not provide independent confirmation. All encountered source/body bans
remain, including rejected variants: D retains 11,194 variants and 31,538 bans;
S/A/J each retain 17,547 variants and 49,965 bans. No final coverage or legality
failure is removed from a denominator.

## Frozen gates and qualification

Both policies have the same gate outcomes. All coverage, qualification, dictionary
legality, median, p90, breadth, fraction and package predicates pass for every
listed comparator. The only failed predicates are strict actions versus D10/D/S/A.

| J comparator | Better / same / worse validation actions | All predicates pass | Failed predicates |
| --- | ---: | --- | --- |
| R | 78 / 19 / 3 | Yes | None |
| seed13 | 40 / 44 / 16 | Yes | None |
| best24 | 22 / 64 / 14 | Yes | None |
| N | 40 / 44 / 16 | Yes | None |
| NCP | 28 / 54 / 18 | Yes | None |
| D10 | 0 / 100 / 0 | No | Strict actions |
| D | 0 / 100 / 0 | No | Strict actions |
| S | 0 / 100 / 0 | No | Strict actions |
| A | 0 / 100 / 0 | No | Strict actions |

P1 (all views decode/qualify) is true; P2 (an atomic fit admission) is false;
P3 (J validation actions below A) is false; P4 (a failed successor gate) is true.
The amendment additionally requires comparison against the record-time current
best before any replacement. Item 24 remains the recorded comparator at this
draft; item 43 has no recorded replacement in the team log. This extra rule cannot
rescue the already failed frozen verdict, so item 41 does not replace current best.
Passing every standing R/13/24/N/NCP comparison supports a future, separately
frozen matched stacking test of these spelling changes. It does not establish
item 41 success or authorize changing its atomic/control comparisons after results.

Qualification reuses only pinned exact (program ID, source hash) passing receipts.
The 21 distinct fresh selected hashes pass all 1,795 strict checks, once per hash;
shared S/A/J choices do not multiply that count. Independent replay rejudges raw
sandbox output and exit/timeout metadata against pinned cases and observations,
without executing candidate code. All ten policy/arm views cover and qualify all
400 programs. Finite strict qualification is not a semantic equivalence proof.

## Costs, execution and scope

Each dictionary costs 2,690 bytes. Fit raw package is 38,944 bytes, or 51,954 with
the 13,010-byte decoder dependencies; validation is 15,014 or 28,024 bytes.
Framing is 41 bytes per packet, payloads are eight bits per selection, and padding
is zero. The shared dictionary is charged once per reported cohort. Offline
encoder source costs 553,906 bytes separately; model bytes and training steps are
zero. Installed runtime footprint remains unmeasured.

Production completed with exit 0 in 1,168.426 supervisor seconds (1,168.283 runner
seconds), under the 3,600-second whole-run cap. Independent replay completed in
143.789 seconds under its separate 900-second cap. Both use cores 0–3 and 8 GiB
limits. No restart, source fallback, arm substitution or threshold change occurred.

Component intent and M1 thresholds are preserved. This is a consumed-development
result, not an M1 success, independent confirmation or default promotion. Protected
and final-heldout populations remain closed. Public evidence contains metadata,
hashes and costs; no source text, dictionary strings, cases or sandbox output.
