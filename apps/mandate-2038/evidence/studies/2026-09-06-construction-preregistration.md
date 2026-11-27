# Construction strategy diagnostic preregistration

Registered before calibration or holdout results on 2026-09-06. This is a policy
diagnostic, not a balance promotion or a human playtest. The user selected a
two-through-five player limit; no other mechanics or numerical incentives change.

## Question and arms

Can a deliberate infrastructure plan afford adjacent connected hosts, construct
a Mega-Cluster early enough to produce, and convert that investment into score
against the same rivals as a simpler Research/Deploy plan?

- Baseline: the existing `infrastructure_compounder` persona and weights.
- `infrastructure_plan_v1`: budget a first Compute-producing Facility beside an
  available Energy site, a second adjacent Facility plus ordinary Generator,
  then a Mega-Cluster; consider Fusion in Era IV. Fund before selecting an
  unaffordable construction. Continue ordinary Research and Deploy choices.
- `research_deploy_plan_v1`: the same immediate action preferences, with one
  Compute-producing Facility and priority on Research and Deploy thereafter.

The focal profile ID stays the same across arms, preserving the policy RNG key.
Both deliberate plans retain the baseline trade, Headline, Influence and Training
stopping procedures. Plans inspect public observations and legal resolutions;
they do not inspect secret selections, future cards, or inject resources. The
planner budgets the current ordinary prices conservatively and leaves actual
costs, discounts, occupancy and eligibility to the engine. It can fail; failure
is retained. It is one bounded plan, not an exhaustive strategy search.

## Frozen sampling

Command: `node lab/cli/construction-study.mjs calibration` or `holdout`.

- Calibration root: `2038-construction-calibration-20260906-v2`; one focal
  faction in seat one, four players, both homogeneous backends, three arms:
  six games. Inspect policy validity before freezing the holdout. Any change
  requires a new calibration identity and disclosure before the holdout.
- Holdout root: `2038-construction-holdout-20260906-v1`.
- Primary: six focal factions × four focal seats × greedy/weighted homogeneous
  backends × three arms = 144 four-player games, 48 matched blocks.
- Completion guards: two, three and five players; six focal factions in seat
  one × both backends × the two deliberate arms = 72 games. These sparse cells
  establish completion only, not faction parity or balance. Two-player evidence
  remains exploratory.
- Every block uses one identical seed and faction/seat roster across arms.
  Rival factions follow canonical order, excluding the focal faction; this
  does not balance every possible omitted-faction combination.
- Rival profiles in seat order are `balanced_operator`, `capability_rusher`,
  `market_maximalist`, and (at five players) `trust_governor`, inserting the focal
  profile at its assigned seat. Profile/faction rotation is explicit, not random.
- Canonical rules overlay `{}`, variable Mandates, negotiation enabled, rich
  projection, one worker, no LLM calls, no intervention scenario. Zero replay
  samples; full raw outcomes and report envelopes are archived and hashed.

## Measurements and validity boundary

Report focal project counts, actual first productive Mega-Cluster Era, productive
project Eras, Compute actually received after caps, final score, paired score
differences, win share, AGI recognition, and action counts. Separate weighted
and greedy results. Check all games reach four Production snapshots. Fusion
connects Facilities and grants its construction award; it does not directly
produce Compute and must not be counted as a productive Mega-Cluster.

Common seeds reduce noise but trajectories consume the shared Training deck and
policy RNG differently. These small, correlated policy samples do not establish
optimal play, balance, human enjoyment, or causal value of each construction.
Do not tune prices or cut mechanics from this diagnostic. An unsuccessful plan
does not prove no affordable strategy exists; a successful one does not prove
people will prefer it. Preserve the earlier 24-game study as historical evidence.

Human reminders, meaningful presence sacrifices, and whether the ending feels
earned require the blind protocol in `docs/playtesting-and-evidence.md`. No human
session is scheduled or completed by this registration.

Calibration collector correction: v1 stopped after archiving its first baseline
report because the collector expected an unwrapped outcome. The runner returns
`{runIndex, outcome}`; the collector now reads that documented shape. Its empty
index and raw report/outcome remain in the local archive. No policy was changed
and no strategy result was used for tuning. Calibration restarts under v2.

Calibration completed all six games. Its index SHA-256 is `52909f3d6ed5f5a3ebd4b927a5b2c38ba3370271e855a1a0c9bc62089fb645f0`. Both deliberate infrastructure games produced a Mega-Cluster in Era III and built Fusion; greedy scores were baseline 12, infrastructure 23, Research/Deploy 17; weighted scores were 14, 20, and 21. These are validity observations, not holdout evidence. No policy or price was changed after calibration. The subsequent fixes concern report viewing, atomic document output, physical-kit protocol, and the card-count test.
