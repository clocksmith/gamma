# Lean balance and cooperative-AGI study

**Evidence type:** deterministic simulation  
**Generated:** July 26, 2026 EDT  
**Purpose:** preserve the historical lean-rules study, identify invalidated
supplier-attribution claims, and point to the clean replacement evidence for
the next controlled physical candidate

> **Correction recorded July 27, 2026:** report schema v3 recorded every seller
> after any imported Power as supporting all newly powered Facilities. It did
> not test whether that seller's Power was necessary. The declarations,
> eligibility, trades, scores, and faction outcomes below remain observations
> of those runs. Every “successful supplier,” supplier top-half rate, and
> candidate–supplier gap conditioned on attributed support is invalidated.
> The exact `0.4.2` reports were also generated with `sourceDirty: true`; their
> embedded hashes describe the state, but commit `ee5dc04` cannot reconstruct
> it. They are historical diagnostics, not release evidence.
> Clean replacement evidence is recorded in
> [`2026-07-27-rc4-clean-evidence.md`](2026-07-27-rc4-clean-evidence.md).

## Hypotheses

1. Removing administrative Power systems while retaining Grid-Ready,
   Realignment, and negotiated supply preserves the game's dramatic decisions.
2. A purpose-built AGI candidate supported by two Power Brokers can declare
   AGI without making the broker strategy noncompetitive.
3. Demis Hassabis's free duplicate protection and starting Trust create too
   much reliable score, while Elon Musk starts too far behind to convert his
   infrastructure identity into a competitive result.

The AGI question is not “can generic bots stumble into a declaration?” The
test route deliberately assigns one candidate, two suppliers, and one Trust
Governor. Because a supplier may sell only one Power, two suppliers are
required to power three candidate Facilities alongside the candidate's basic
grid connection.

## Rules and engine identity

- Baseline implementation commit: `ee5dc04`
- Baseline executable: `0.4.0`
- Baseline physical candidate: `0.4.0-rc.1-lean`
- Baseline coverage: `lean-grid-ready-v1`
- Superseded executable: `0.4.2`
- Superseded physical candidate: `0.4.0-rc.3-test`
- Superseded coverage: `lean-grid-ready-v3`
- Replacement executable: `0.4.3`
- Replacement physical candidate: `0.4.0-rc.4-test`
- Replacement coverage: `lean-grid-ready-v4`
- Replacement report schema: `4`
- LLM decisions: none
- RNG: Mulberry32 v1

Generated JSON reports remain in `studies/simulation/` as local raw evidence
and are intentionally ignored by Git. This receipt is the tracked
interpretation and change record.

## Primary reports

| Purpose | Raw report | SHA-256 |
| --- | --- | --- |
| Initial targeted cooperative route | `20260727T030010608Z-tournament-0-4-0-c176175e5a03-lean-two-brokers-evidence-v1-500x4-cli.json` | `9bb9a1f0896fadbf878120f82d6045279b0892c28ff8091f73dd550c3e6174a2` |
| Initial diverse faction cohort | `20260727T030049402Z-tournament-0-4-0-c176175e5a03-lean-diverse-evidence-v1-500x4-cli.json` | `4d951111541730f06059dea10c78bca913c481b3c4734c2161e84054b832ac7e` |
| Intermediate Trust-only adjustment | `20260727T030156911Z-tournament-0-4-0-85ef72513de7-lean-diverse-evidence-v1-500x4-cli.json` | `34c00af7389861e826349500026d570df9e653f1d9f78540bee5bffdf3464ea7` |
| Final diverse faction cohort | `20260727T030336686Z-tournament-0-4-0-ddcba079ab6f-lean-diverse-evidence-v1-500x4-cli.json` | `e1f71a15d3f414b0866131b05d8c481c9624e691450697913eb0e1405df254d7` |
| Final targeted cooperative route | `20260727T030413173Z-tournament-0-4-0-ddcba079ab6f-lean-two-brokers-evidence-v1-500x4-cli.json` | `2c865d09d7579fc7d4b7d80ba5e75cb3b20b06ee0decf4aa5bd6742efb033f24` |

All primary cohorts use 500 four-player matches. The diverse cohort rotates
Balanced Operator, Capability Rusher, Infrastructure Compounder, and Market
Maximalist profiles across factions and seats. The cooperative cohort rotates
one AGI Candidate, two Power Brokers, and one Trust Governor.

## Findings

### Cooperative AGI is rare but real

The initial generic and nominal cooperative profiles produced no
declarations. Replay inspection showed a policy defect, not a rules verdict:
generic consequence scoring preferred a lexicographically earlier empty Power
allocation, suppliers did not spatially approach the candidate, and one broker
could never provide both missing Power.

After adding explicit consequence weights, partner preferences, visible
opponent sites, and two Power Brokers, the final 500-match cooperative cohort
produced:

- 13 declarations in 500 matches (`2.6%` of matches);
- 13 Genuine AGI endings;
- candidate eligibility in `6.4%` of matches;
- 703 completed Power sales (`1.406` per match);
- Power Broker mean score `17.715`;
- Power Broker win share `29.1%`.

This establishes a deterministic, rules-legal route. It does not establish
that humans will discover it or agree to it.

### Historical supplier result is not causal evidence

Power Brokers were competitive across the entire cooperative cohort, exceeding
the neutral four-player win-share benchmark. The historical `30.77%`
successful-supplier top-half rate and candidate-gap figures are withdrawn:
schema v3 accumulated sellers without proving that their imported unit was
necessary for the declaration's Grid-Ready Facilities.

Schema v4 instead performs a per-allocation counterfactual: a seller is
attributed only when removing that seller's imported Power would make the
selected powered demand infeasible. Supplier viability remains the bargaining
question, but only a clean v4 cohort may answer it.

### Faction outliers narrowed without rewriting identities

The first diverse cohort produced faction win-share spread `0.3279`, with
Demis Hassabis at `41.7%` and Elon Musk at `8.9%`. A Trust-only adjustment
narrowed the spread to `0.2664`. The final adjustment produced:

- faction win-share spread `0.2065`;
- seat win-share spread `0.041`;
- action diversity `0.9286`;
- Demis Hassabis win share `34.94%`;
- Elon Musk win share `14.29%`.

This is a substantial automated-pressure improvement, not proof that the
factions are balanced for humans. Strategy-profile spread remains meaningful,
and the simulator's negotiation is intentionally bounded.

## Selected changes

- Preserve Grid-Ready markers and the mandatory Round III Realignment.
- Preserve four ordinary Build opportunities as the cost of a self-sufficient
  AGI route; do not relax the declaration contract before human negotiation.
- Reduce Demis Hassabis's starting Trust from 4 to 3 and starting public
  Mandate from 4 to 2.
- Make Scientific Method an optional once-per-round protection costing 1
  Runway when it actually prevents a duplicate crash.
- Increase Elon Musk's starting Trust from 1 to 2, Compute from 2 to 3, and
  starting public Mandate from 0 to 2.
- Add AGI Candidate and Power Broker personas plus spatial-partner and
  consequence preferences so intended strategies can be tested rather than
  inferred from generic bots.
- Log Power bought, Power sold, supplier compensation, candidate eligibility,
  cooperative declarations, supplier placement, and candidate–supplier gaps.

## Rejected changes

- Do not delete Grid-Ready based on generic-policy zeroes.
- Do not replace demonstrated operation with a declaration-time capacity
  proof.
- Do not weaken AGI requirements merely to raise declaration frequency.
- Do not claim that a `2.6%` scripted declaration rate is a human balance
  target.
- Do not automatically compensate suppliers until human negotiation evidence
  shows that the deal is individually irrational at the table.

## Final release stress tests

After generating the immutable `0.4.1` release, four additional cohorts tested
the exact ruleset fingerprint
`sha256:57c7ef511a804606170a075f5e31539d393adfd73dae99925f064d6110c4d362`.

| Players | Runs | Seat spread | Faction spread | Action diversity | Raw report / SHA-256 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2 | 200 | `0.130` | `0.2794` | `0.9382` | `20260727T030946163Z-tournament-0-4-1-57c7ef511a80-lean-final-p2-200x2-cli.json` / `0c4ed42d3335bf103571b1860651fdb14a8bfc402c838dafa4d43acc8a8c55a1` |
| 3 | 200 | `0.025` | `0.4141` | `0.9360` | `20260727T030947564Z-tournament-0-4-1-57c7ef511a80-lean-final-p3-200x3-cli.json` / `b96044ae5a59d8c03dff27aa715024df88538ace14474999cedfc007c1a752f9` |
| 5 | 200 | `0.0425` | `0.2088` | `0.9492` | `20260727T030950387Z-tournament-0-4-1-57c7ef511a80-lean-final-p5-200x5-cli.json` / `1e67120a1a25c9d6670c3d2b9c42e8d6dff910f76788b4887b48a630a061dd37` |
| 6 | 200 | `0.130` | `0.2200` | `0.9373` | `20260727T030951276Z-tournament-0-4-1-57c7ef511a80-lean-final-p6-200x6-cli.json` / `51e023c67d99f1a1df4315f1b0d5a15a80c535bce93f554aead532f336dfbdf5` |

The cohorts completed without policy fallbacks or invariant failures. They
support explicit two- and six-player scaling tests rather than a claim that
one map and policy mix are already balanced at every count.

Those reports remain valid ruleset evidence, but executable `0.4.2` supersedes
their engine after a final regression found that Scientific Method could
incorrectly refund its Runway when an ordinary Safety token or Research-campus
protection was consumed. The rules value did not change; the engine now charges
only when Scientific Method itself protects the run. Exact `0.4.2` confirmation
reports are listed below.

| Exact `0.4.2` cohort | Result | Raw report / SHA-256 |
| --- | --- | --- |
| Diverse strategies, 500 × 4 players | faction spread `0.1783`; seat spread `0.051`; action diversity `0.9292`; one eligible seat and no generic declaration | `20260727T031455539Z-tournament-0-4-2-1cfb69d6f5cb-lean-final-042-diverse-500x4-cli.json` / `2ba19e633bfeda2459882555ca448e56a2487c7573dcaf0a9d9704efd7ab5c94` |
| Candidate + two Brokers + Governor, 500 × 4 players | 11 declarations and Genuine AGI endings (`2.2%`); 691 Power trades; Broker win share `29.85%`; supplier-conditioned metrics withdrawn because attribution was non-causal | `20260727T031453509Z-tournament-0-4-2-1cfb69d6f5cb-lean-final-042-cooperative-500x4-cli.json` / `665ff66f444f60b1dd59a082dfdb5f11f07605bd2a298ee6da5438b46c4f94a3` |

The pre-fix bounded rule search tested 12 variants over 80 four-player matches
each. It recommended iteration 0—the unchanged canonical values—with fitness
`1.624`, faction spread `0.1786`, action diversity `0.9284`, and no generic
AGI declarations. Its historical report is
`lean-final-balance-0.4.1.json`, SHA-256
`dc2bfe0ba1e0f7d107f484d6e25161eea6fbf3abf2271bb99870de3d33de5673`.

The exact `0.4.2` rerun proposed an accumulated hill-climb package containing
Audit multiplier `1.1`, Venture Fund `5`, and Venture Scrutiny `1`. It reduced
sampled faction spread from `0.2411` to `0.2054`, but worsened profile spread
from `0.2938` to `0.3438`, produced no generic declaration, and bundles three
numbers rather than isolating a causal rule. It was rejected. The report is
`lean-final-balance-0.4.2.json`, SHA-256
`4a695acac01f900d6980cef3cb0f8974fd800c5da680a48812c096eebbee89ab`.
No optimizer proposal was promoted.

A four-generation, six-candidate strategy evolution used 12 matches per seat.
Its champion emphasized Research and Build and reached sampled mean win share
`0.3333`, but its seat results ranged from `0.0833` to `0.5833`. That sample is
too small and seat-sensitive to replace the Balanced Operator. The complete
candidate remains in `lean-final-evolution-0.4.1.json`, SHA-256
`6cc7754ce5a319e3c42663e370eb0f460e74c483be1ea1bf5375366cef875e0b`.

## Affected-surface audit

- **Semantic graph:** Power, faction, strategy, rules-version, and simulation
  descriptions updated.
- **Rulebook:** lean Power production, immediate purchases, removed baseline
  Upgrades, restricted faction timing, and final faction values rendered from
  the graph.
- **Machine data and references:** regenerated from the same graph.
- **Prototype and replay:** use the selected-rules engine and canonical
  decision packets.
- **Simulation:** updated legal decisions, strategy schema, weighted policy,
  cooperative personas, instrumentation, and report aggregates.
- **Docs and gallery:** regenerated and version-aligned.
- **Tests:** contract, engine, faction, Power, strategy, replay, and report
  assertions updated.
- **Releases:** immutable executable and physical-candidate bundles regenerated
  under their final identities.

## Validity boundary and next evidence

These results compare deterministic policies inside one implementation. They
can expose unreachable routes, policy defects, faction pressure, and invariant
violations. They cannot measure teachability, delight, threat credibility,
human bargaining, kingmaking, table trust, or session duration.

The next authority is clean schema-v4 simulation evidence followed by one
controlled four-player physical test using `0.4.0-rc.4-test`, with supplier
offers, compensation, placement entering Round IV, declaration timing, rules
lookups, and full duration recorded. The replacement simulation receipt must
name a clean source commit and exact raw-report hashes.
