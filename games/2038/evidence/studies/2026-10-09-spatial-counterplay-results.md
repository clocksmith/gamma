# Spatial choices and counterplay — 2026-10-09

**Result: placements demonstrably affect outcomes; robust counterplay and the
specific value of hex adjacency are not established.** The registered study
passed one of six gates. This neither qualifies the map nor proves an
unanswerable strategy. No geography, scoring or default-policy change was made.

Sources: [registration](2026-10-09-spatial-counterplay-preregistration.md),
[spatial receipt](2026-10-09-spatial-counterplay-receipt.json), and
[combined verification](2026-10-09-spatial-counterplay-verification.json).
The latter records archive paths and hashes for the complete game outcomes,
unified audit, browser walkthrough and test logs.

## Method and identity

Clean commit `9dc8b5c475d7ed143d13873b4e0937087286cb57`; executable 0.22.2,
engine 0.25.2, rules 0.12.0-rc.16-test. Mechanics are identical to 0.22.1.
The executable repairs a public-information defect: Venture responders formerly
received accept/reject choices without proposer, hosts or reciprocal income.
Those public terms now reach both policies and the browser. No hidden deck or
opponent selection is exposed; pending terms clear after every response.

Nine fixed public-only placement/consent heuristics were searched in three
separate 48-block stages: champion, individually useful response, then adaptation.
Ordinary action bundles remain unchanged. Plans freeze before confirmation on
576 unused seeds: 144 three-player, 192 four-player and 240 five-player blocks.
All six factions, seats and homogeneous weighted/greedy backends are covered.
Half the blocks use ordinary policies; half use the same existing construction
scaffold at every seat. Scaffold games exercise infrastructure deliberately and
are reported separately from ordinary play.

There were 4,799 spatial game executions: 1,296 search, 3,456 confirmation and
47 one-placement branches. A separate unified audit ran 480 matches; the
66-game execution smoke has no qualification authority. Executions are not
independent samples. Adaptation selected the champion again, and the alternative
selected the immediate-resource plan. Their corresponding confirmation arms
are exact duplicates on every seed. Four-player paired inference uses 192
blocks, not thousands of independent observations.

## Held-out results

Selection: district-control champion, immediate-resource responder, unchanged
district-control adaptation, immediate-resource alternative. Win share means
fractional winner credit, including shared ties.

| Four-player arm | Focal win share | Focal score | Responder win share |
| --- | ---: | ---: | ---: |
| Ordinary authored policies | 20.31% | 17.48 | 29.17% |
| Control against ordinary rivals | 38.02% | 19.71 | 20.83% |
| Control against immediate responder | 30.73% | 19.34 | 33.85% |
| Immediate-resource focal against ordinary rivals | 40.10% | 19.76 | 19.79% |

The responder gained 13.02 percentage points of winner credit and 2.43 score;
the champion lost 7.29 points of winner credit. These are promising point
estimates, not qualified counterplay. The eight preregistered win-credit effects
use Bonferroni-adjusted bounded intervals; the primary interval radius is
24.51 percentage points. Counter own-gain and champion-suppression intervals
both cross zero. Control versus immediate is -2.08 points, with interval
[-26.60, +22.43]. Adaptation changes nothing: same policy, identical outcomes.
Secondary score intervals are descriptive and unadjusted.

Ecology matters. Control wins 51.04% against ordinary four-player rivals but
25.00% in the shared construction scaffold; immediate wins 50.00% and 30.21%.
Beating weak authored placement is not automatically a rules exploit. No Power
or partner plan established an advantage over immediate-resource placement.

## Direct placement witness

Of 48 scheduled rival-placement replays, 47 had an eligible legal alternative
with identical category, Agent, action bundle and immediate costs. Changing
only that rival placement changed subsequent focal locations in 39 branches,
final focal scores in 29, and focal winner credit in three. **27 branches changed
both locations and scores**, satisfying the exact first registered gate. The
runner's separate aggregate counts alone would not establish that conjunction.

For seed `spatial-20261009-confirmation-4-0-0-greedy-1`, rival seat 1's first
Cloud Facility moves from `cloud-3` to `cloud-2`, using `s1-agent-1` and two
Runway in either case. Dovetalis at seat 0 subsequently changes an Era III
placement from `cloud-2` to `cloud-1`, finishes with 24 rather than 26 Mandate,
and loses its former winner credit. This is an actual complete-game legal replay.
Later decision counts and random consumption can diverge; it does not isolate
Power as the cause or demonstrate optimal responses.

## Limits and next decision

The fresh unified audit has zero integrity violations but remains
`outside_provisional_bounds`, with precision unmet and nine observed threshold
failures: three-player seat/faction/profile spreads and winning-path entropy/top
share; four-player seat/profile spreads; five-player profile spread/top share.
No registered dominance or pairwise-dominance flag qualified. Sparse coverage
cannot turn that absence into a balance claim or identify geography as the cause.

These are bounded heuristics, not an optimal solver. Denial primarily values
scarce construction slots; consent uses a simple leader heuristic; adaptation
does not learn a new policy. Human understanding and enjoyment remain untested.
District control can exist without hex adjacency. All tested arms still obey
the existing Power/Venture adjacency rules, so this study cannot establish
that removing adjacency preserves play.

A further current-rule counterplay test needs a separately frozen stronger
control-denial/adaptation treatment and fresh confirmation seeds. To judge
removal, select and register one concrete adjacency lever, preserve shared
district competition, and compare complete games with matched factions, seats,
policies and seeds. Experienced human sessions must separately test whether
opponents' locations produce understandable, useful responses. Neither change
is promoted by this result.
