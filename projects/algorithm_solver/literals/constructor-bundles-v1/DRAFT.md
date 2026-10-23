# Atomic constructor/operand bundles — item 39 design

Status: root approved this exact four-arm scope, caps and resource budget.
Implementation is prepared for independent prelaunch review in FREEZE.md.
No private-source access, corpus run or commit is authorized by this document. The parent is item 32, recorded at `5d0ee7ccd`; its frozen code and
results remain unchanged. [prototype.py](prototype.py) implements only candidate
construction and one atomic exact trial, with [five synthetic tests](test_prototype.py).

The source cohort is **item 30 D11**, fixed now before any item 39 private probe.
Do not substitute item 32’s searched literal dictionary or another item 30 arm.
All four proposed arms start from D11’s identical dictionary and sources under
item 32’s canonical min-N/lexicographic-ID policy. The same consumed fit 300 /
validation 100 partition and exact source qualification receipts apply.

## Evidence and the concrete search restriction

Item 32 recorded 8,324 validation actions for searched literal/prefix and 8,334
for template/union. Prefix retained and used no P entries. Template/union retained
one I entry used on one validation program, saving seven actions locally against
literal but losing globally through slot replacement. All 2,000 views decoded;
no structured arm passed its gates. These are disclosed prior observations, not
item 39 predictions or evidence against every search method.

The code contains a real *local admission barrier*:

- `codec.expression` accepts a P operand only as one complete literal expression
  or a recursively valid P expression. Several adjacent literal tokens cannot
  silently become one operand. I requires each whole identifier as a paid literal.
- `search.optimize` adds at most one absent key per trial and accepts only strict
  total fit-N reductions. A constructor with missing operands is unusable.
- A missing operand literal need not improve ordinary literal encoding by itself:
  existing chunks may cross its boundary and remain cheaper. Such an operand
  cannot be installed through an equal-N intermediate state.
- At capacity, missing keys also require simultaneous removals. Mandatory initial
  characters stay protected. The existing deletion shortlist can screen out
  useful joint removals; this remains a separate limitation, not a proven cause
  of item 32’s result.

This establishes that individually rejected keys can be complementary. It does
**not** establish that the actual item 32 corpus stopped at this barrier, that no
literal-merge route can bypass it, or that atomic constructors will beat literals.
No private instance has been inspected to make that stronger claim.

The caching concern is settled without changing item 32. Rows store literal and
constructor **keys**, not cached numeric IDs. `codec.order` has a fixed order on
keys; inserting or removing an unused key preserves relative order among every
admissible old plan. Lexicographic tie winners therefore remain unchanged. New
packets derive their numeric IDs from the new dictionary. A synthetic real-JS
fixture checks an absent key inserted before used keys: payload IDs change,
cached and fresh canonical plans agree, independent decode succeeds, and removing
the key restores the original packet. New operands that appear in a source already
invalidate the cache; absent constructors cannot create a matching AST edge.

## Synthetic counterexample and its limit

Four invented programs use the Cartesian product of `longAlpha`/`longGamma` and
`longBeta`/`longDelta` as arguments to `Math.max`. The seed covers each call with
four overlapping-boundary chunks and each surrounding wrapper/suffix with one
literal. Both operands occur in at least two distinct programs. The actual item
32 AST extractors, planner, typed dictionary and independent Node decoder are
used unchanged.

Total seed N is 24. Adding the P shape alone, either operand alone, or any pair
from `{constructor, longAlpha, longBeta}` leaves N at 24 and uses no constructor.
Adding all three atomically gives N=23, with one root and **two paid argument IDs**.
The same result holds for the I shape. At exactly 256 slots, replacing three
explicit unused seed literals with the three additions preserves all mandatory
characters and produces the same gain; every proper subset still gives N=24.
Unused seed literals remain fully charged in that capacity fixture.

The typed dictionary grows enough that the full raw package increases despite
the one-selection saving. Moreover, a shared literal `Math.max(long` gives N=20.
That control is included as a passing test, not omitted. This fixture proves
local atomic reachability only; it neither proves readiness nor a constructor
advantage over item 32’s entire literal-merge search.

## Matched 2-by-2 comparison

| Arm | Entry kinds | Admission moves |
| --- | --- | --- |
| L1 | L only | One-key add/swap, matched deletion strategy |
| T1 | L+P+I | Same one-key moves; no atomic installation |
| LB | L only | L1 plus bounded literal bundles |
| TB | L+P+I | T1 plus the identical LB bundles and constructor/operand bundles |

All use the identical D11 seed, partition, common fit extraction, pooled literal
opportunities, capacity, mandatory character subset, exact encoder, acceptance
rule and trial/time limits. T1 is necessary: comparing TB only with historical
item 32 would confound atomic moves with the newly exposed operand literals and
search details. LB is necessary: ordinary literal bundles may gain from the same
larger move size. No later choice of source cohort or winning arm is permitted.

P and I share the typed arms here. This is not a new P-versus-I factorial or a
claim of additive stacking. Actual P/I-use subsets remain visible descriptively.

## Exact pool and bundle enumeration

The following bounded procedure is root-approved and implemented; execution
still requires the independent freeze review.

1. Retain item 32’s fit-only constructor eligibility and caps: at least two
   distinct program IDs; at most 32 P and 64 I keys under its existing ranking.
   Retain its common AST-span literal pool of at most 256 entries.
2. From instances of those retained constructors, collect P’s complete direct
   expression operands and I’s distinct identifier arguments. A new operand
   literal must occur as such an operand in at least two fit programs, have
   length 2–160, and pass the same full-source/body bans. Existing one-character
   operands remain usable; do not introduce missing characters through this pool.
   Cap the common operand pool at 256, ranked by summed `(length−1)` across paid
   argument positions, then length and text. Program support counts IDs, not
   repeated uses within one program. All four arms receive the same operand pool.
3. Each instance proposes one shape plus its actual literal operands, removing
   keys already present. Reject it if any missing operand is ineligible. There
   are at most five absent keys: one constructor plus at most four distinct I
   arguments; direct P has at most three operands. No new nested constructor
   dependency tree is mined. Already-present constructors may receive missing
   operands through the same rule. Deduplicate exact ordered addition sets.
4. Rank these bundles by descending distinct supporting instance-program count,
   then summed fixed/repeated generated bytes over those instances, then ordered
   key tuple. Retain at most 12 P and 12 I bundles per round. Their missing-literal
   operand subsets, after deduplication and removing empty/singleton sets, form
   at most 24 common operand packs available to **both LB and TB**.
5. All arms offer the same one-key literal list: up to 24 current contiguous
   literal merges, 24 further item 32 common-pool literals, and 24 further operand
   pool literals, deduplicated in that order. Typed arms additionally offer all
   absent allowed constructor keys (at most 96), interleaving the existing P/I
   rankings. This changes availability relative to item 32, but it is matched
   within item 39.
6. LB and TB share an additional deterministic literal-bundle list. On the
   ranked one-key literal list, take the first eight consecutive windows of
   length 2, then 3, then 4, then 5 (at most 32 sets), and append the at most 24
   operand packs above. Deduplicate exact sets. This is at most 56 common literal
   bundles. There is no combinatorial subset search over the entire pool.
7. Enumerate candidate streams round-robin in the fixed order: one-key literal,
   common literal bundle, one-key constructor, constructor/operand bundle. Skip
   streams absent from an arm and exhausted streams. This exposes atomic moves
   before a long singleton pass consumes the time budget. Each available stream
   retains its own deterministic order; duplicate final dictionaries are tested
   at most once per round.

The prototype demonstrates the local barrier independently of the bounded
optimizer. optimizer.py implements the approved rankings, streams and deletions;
run.py and report.py preserve sealing and independent packet/cost replay.

## Deletions, capacity and exact scoring

At every round probe each removable current key once, preserving exactly the
initial character subset. Record the exact full-fit N loss; coverage failure has
infinite loss. Keep the 12 lowest-loss keys, ordered by loss then key, exactly the
same shortlist in each arm’s current state. Infeasible deletion-only entries
remain eligible but may be screened out by this cap, as in item 32.

For a candidate’s distinct absent-key set A, let
`r = max(0, current_entry_count + |A| − 256)`. If r=0, test the empty removal set.
Otherwise enumerate the at most `choose(12,r)` removal combinations, rank by sum
of deletion-only losses then ordered keys, and evaluate only the first **12**.
Since `|A|<=5`, enumeration is bounded by 792 combinations, without encoding those
screening combinations. No mandatory character may be removed. Singletons use
r=1 at capacity, so L1/T1 retain the ordinary 12 single-swap removal choices.
Every arm has the same capacity, removal cap and evaluation budget; no extra
slots, free operands or coverage fallback are granted to atomic moves.

Apply additions and removals in one transaction. Encode every fit source under
the resulting dictionary, counting every root, every recursively paid P argument,
every I identifier argument and Finish. Reject any coverage loss or legality
failure. Use the unchanged canonical min-N/lexicographic-ID policy. Accept only
strict lower total fit N; ties among improving candidates use complete serialized
raw package bytes, then ordered keys. Equal-N intermediate states stay rejected.
Fully charge typed metadata and the complete mixed decoder/Acorn, even when no
constructor survives. Literal controls retain their separate literal decoder.

A round accepts the best evaluated strict improvement. If the bounded proposal
list is exhausted without improvement, label it `bounded_neighborhood_no_improvement`,
not a global optimum. The shortlist and 12-combination cap deliberately leave
some joint-removal opportunities unsearched. Report that limitation and coverage
rejections; do not attribute every miss to the constructor grammar.

Approved equal limits: 10,000 evaluated dictionaries / 300 seconds per arm,
including initial state, deletion probes, candidates and coverage failures.
The 300-second check is between exact dictionary trials; one in-progress trial
can overrun. Each trace trial includes its actual elapsed seconds; summary reports
actual total search time, overrun and longest recorded trial. The supervisor
hard-stops the whole process group at 1,800 seconds.
Every evaluation increments the same counter, whether the safe item 32 cache
reuses unaffected rows or fresh plans are needed. Extraction/pool construction
is inside the 1,800-second whole-job guard. Four single-core workers,
8 GiB per worker, OMP/BLAS1; L1/T1/LB/TB use cores0/1/2/3 respectively; root assigns the nonoverlapping
launch queue with item38. Partial/time-failed supervision invalidates the experiment and
retains all artifacts. No additional search is permitted after validation.

## Reporting and conditional attribution

Seal all four fit dictionaries, pools, source identities, traces and costs before
validation source values are loaded. Reuse only the unchanged D11 ID/source-hash
qualification receipts; no new execution or repair is scheduled. Validation may
not change bundle limits, pool caps, grammar, dictionary or source cohort.
Independent reporting must reconstruct exact packet IDs, sources, canonical plans,
constructor/argument counts, generated bytes, body/half-source guards, full costs
and every coverage denominator, using item 32’s independent typed decoder.

Report whole-cohort paired effects L1/LB, T1/TB and LB/TB, all failed predicates
and search-trial/time composition. On the same IDs additionally report the
per-program difference-in-differences
`(TB actions − T1 actions) − (LB actions − L1 actions)` as a descriptive interaction
of the two search factors. It does not replace gates or establish generalization.

Retain item 32’s six exact-ID descriptive subsets: common pool eligible, arm pool
eligible, P used, I used, either used and both used. Pair each structured arm with
L1, LB and untouched D11 on exactly those IDs. Report full dictionary and decoder
costs for each subset, overlapping/nonadditive membership, null ratios for empty
sets and unavailable totals for missing coverage. Add fit-only admission metadata:
number of accepted atomic moves, number supplying missing operands, constructor
uses before/after those moves, all rejected proper-singleton scores if evaluated,
and literal-bundle/control gains. Do not infer a complementary barrier from an
accepted bundle without those recorded singleton comparisons; untested proper
subsets remain unknown, not assumed nonimproving.

Readiness retains item 32’s full gates with **LB as the matched literal
control**: all 400 exact decode/qualification, legal <=256 entries; >=5% validation
action reduction, strict median/p90 improvement, >=60/100 improve, <=25 worsen,
nonincreased C/N and raw package <=105% of LB. TB must additionally beat both T1
and untouched D11 in total actions, with non-worse median/p90/C, <=25 worse and
raw package <=105%. Decoder-inclusive costs remain visible. No alternative arm
may replace a failed TB claim post hoc. Conditional gains are retained even if
whole-cohort readiness fails. This is separate 2c evidence; flat M1 and its
selected/default candidate do not change.

## Review and launch gates

Root approved the four arms, operand cap256, round robin, twelve deletion
combinations,10000 trials/300 seconds each and1800-second whole-job guard.
Implementation and synthetic checks require root/Claude review and a pushed
freeze before private loading. Root controls the nonoverlapping queue with38.
Public item32 contract metadata pins D11 identities without private probes.

M1 remains 400/500, <=256 shared entries, median<=32/p95<=96 selections,
<=10% single-character selection bits and zero whole-solution entries. Existing
P/I grammar limits, half-source generated-byte rule, expansion/output limits,
paid-argument semantics and exact source/body exclusions remain unchanged.
Component intent and protected-data boundaries are preserved.
