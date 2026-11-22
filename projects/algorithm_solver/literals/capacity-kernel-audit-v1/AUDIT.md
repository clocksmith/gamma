# Audit of the nullspace-kernel theorem and its "+1" lift

By `claude-bits-1`, 2026-11-22 (UTC), against `capacity-diagnostic-v1/diagnostic.py` as of Gamma `30c74bee`
(the version with the two fixes). The theorem is stated in `capacity-race-v1/PREREGISTRATION.md`. This is
an audit, not a pre-registered experiment: nothing was predicted beforehand.

**Verdict: I could not break it.** The slack argument holds line by line, the code made no wrong call in
11,466 exhaustive checks, and on 23 real corpora the theorem alone gives the exact minimum on 20.

## The argument, checked line by line

Notation: blocks B after forced cuts, their vectors span a space R of dimension r = |Σ| − d.

| Step | Claim | Why it holds |
| --- | --- | --- |
| 1 | A dictionary of r entries has every entry's vector in R | It spells every block, so its span contains R; with only r entries the span equals R. |
| 2 | It contains no single character outside S_det | A single character c has vector e_c, and e_c lies in R exactly when no kernel vector is nonzero at c. |
| 3 | So every occurrence of a character of S_free lies inside a multi-character entry that is orthogonal to the kernel | Steps 1 and 2. These entries are the set called E_span^free. |
| 4 | r = \|S_det\| + k_free | k_free is defined as \|S_free\| − d. |
| 5 | A maximal run of positions that no E_span^free occurrence covers, bounded on each side by a block edge or an S_free character, is spelled by entries that avoid S_free | No S_free-touching entry can cover a position of the run; an entry that avoids S_free cannot extend over the S_free character beside the run. So the run's ends are cuts of the spelling. |
| 6 | The entries that avoid S_free number at least the rank of those runs | The rank bound, applied to the runs. |
| 7 | So the S_free-touching entries number at most k_free + Δ | Steps 4 and 6, with Δ = \|S_det\| minus that rank. |
| 8 | Replacing every other entry by single characters of S_det still spells every block | Each such entry is a string over S_det. |
| 9 | If no set of at most k_free + Δ entries from E_span^free spells the blocks together with S_det, no dictionary of r entries exists | Steps 3, 7 and 8. Hence the minimum is at least r + 1. |

Points I looked at for a gap and found none:

- **Two prime fields.** S_free is the union of the kernel supports over the fields that attain the rank.
  Step 2 needs e_c in R in every such field, which is what the union gives. The pre-registration's wording
  of S_free is loose; the code is right.
- **Whole programs as single characters.** The necessity search allows every character of S_det, which can
  only make the lift harder to fire. The construction path is verified against the real rule.
- **The search is complete unless it aborts.** It branches on every candidate for the hardest uncovered
  occurrence; when all occurrences look covered but a block still does not spell, it branches on every
  entry that crosses the reachability frontier of that block. An aborted search returns `UNRESOLVED`.
- **Dropping longer entries with the same coverage** is safe: the longer entry is the shorter one with
  S_det characters on each side, which single characters can spell.

## Test 1: the theorem's code alone against exhaustive search

`audit_kernel.py` calls `nullspace_kernel_certificate` directly, so no other tier, fallback or heuristic
can answer for it. 5,733 small corpora in five families, under both rules.

| Outcome | Count | Wrong |
| --- | ---: | ---: |
| `RANK_ATTAINED`, with a dictionary of exactly rank entries | 1,878 | 0 |
| `RANK_UNATTAINABLE`, the +1 lift | 3,506 | 0 |
| `SATURATED` | 6,056 | 0 |
| `UNRESOLVED` | 26 | all have Δ of 1 or more |
| Left unresolved inside the claimed exact class (Δ = 0) | 0 | |

## Test 2: the theorem alone on 23 real corpora

`kernel_alone_real.py`; every dictionary it builds is replayed with the capped checker of
`capacity-boundary-v1`.

| Outcome | Corpora | Exact minimum known from rank and kernel alone |
| --- | ---: | ---: |
| Rank equals the alphabet | 12 | 12 |
| Rank attained, dictionary replayed | 8 | 8 |
| Rank unattainable, +1 | 3 | 0 |
| **Total** | **23** | **20** |

- The eight constructions: 61, 62, 65, 65, 65, 66, 68, 68 entries. Six agree with minimums established
  earlier by a checked certificate and a replayed dictionary; the other two (race B07 and B11) had no
  independent minimum before.
- The three lifts: JS-2 from 64 to 65, which matches its independently established minimum; PY-3 from 51
  to 52 and B04 from 22 to 23, which are far below the best dictionaries known (62 and 60) and are not
  independently confirmed.
- Longest run: 3.2 seconds.

## What rank alone and rank plus kernel settle, on these 23

| Budget asked | Rank alone | Rank plus kernel |
| --- | ---: | ---: |
| The rank bound itself | 12 | 23 |
| One above it | 14 | 20 |
| 64 entries | 19 | 21 |

Rank alone answers "fits" only when the alphabet already fits. At 64 entries the kernel adds one rejection
(JS-2) and one construction (B11); PY-3 and B04 need the separate heuristic constructor.

## Limits

- These 23 corpora were already seen by this project. The external three-arm race is the unseen test.
- The audit checks the lift, not its strength: it is +1 and no more.
- Eligibility on real corpora (the shared-substring table, the 160-byte cap) is checked here only through
  the replayed dictionaries and the one independently confirmed lift.
- Whether the theorem is new is not assessed here.
