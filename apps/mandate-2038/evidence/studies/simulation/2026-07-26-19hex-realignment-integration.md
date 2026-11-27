# Nineteen-Hex And Realignment Integration Study

**Study ID:** `2026-07-26-19hex-realignment-integration`
**Evidence:** automated simulation, not a human playtest
**Generated:** July 26, 2026 at 18:13:46 UTC
**Raw local report:** `2026-07-26-19hex-realignment-integration-64x4.json`
**SHA-256:** `c4124767cf33e5ee678e4e93c36e17fd7812390b58b0fab7ab3f16bc4561a87b`

## Configuration

- 64 complete four-player matches.
- Seed: `19hex-realignment-integration`.
- Environment: `selected-rules-v2`.
- Personas: Balanced Operator, Capability Rusher, Infrastructure Compounder,
  and Market Maximalist.
- Backends: seeded weighted policy for every seat; no Claude or Codex calls.
- Factions and personas rotated independently. Sixty-four runs contain four
  complete repetitions of the sixteen faction/persona pairing schedule.
- One sampled replay was retained.
- Canonical rules variant: no numerical override.

## Hypothesis

This was an integration study of a user-selected rule, not a search that
selected the rule:

1. Every generated board contains one center, six inner-ring, and twelve
   outer-ring spaces.
2. Every complete match resolves exactly four simultaneous secret
   Realignment votes.
3. Ring motions preserve nineteen tiles and complete the final vote before
   endgame scoring.
4. The new decision stage does not collapse the six Core Action choices or
   prevent matches from settling.

## Aggregate results

| Measure | Result |
| --- | ---: |
| Completed matches | 64 / 64 |
| Expected Realignments | 256 |
| Recorded Realignments | 256 |
| Consolidate the Core | 94 |
| Expand the Periphery | 80 |
| Authorize Counter-Cycle | 82 |
| Sampled replay Realignments | 4 |
| Tiles in final sampled board | 19 |
| Core Action diversity | 84.02% |
| Faction win-share range | 42.19 percentage points |
| Persona win-share range | 12.50 percentage points |
| Seat win-share range | 18.75 percentage points |
| AGI eligibility | 0.39% of player-matches |
| AGI declarations | 0 |
| Secret-objective completion | 7.03% |
| Mean Systemic Risk created | 0.84 per match |

### Factions

| Faction | Win share | Mean Mandate | Capability | Customers | Facilities | Audit hits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Imperial Research Lab | 51.56% | 22.20 | 7.66 | 2.34 | 1.34 | 3.05 |
| Platform Empire | 26.56% | 19.83 | 6.59 | 2.28 | 1.52 | 3.23 |
| Vertical Empire | 12.50% | 15.52 | 6.31 | 1.67 | 1.30 | 3.89 |
| Coalition Lab | 9.38% | 16.53 | 5.75 | 1.27 | 1.33 | 3.41 |

## Interpretation

The four integration hypotheses passed. The environment completed every match,
resolved the expected four ballots per match, preserved the complete
nineteen-space board, and retained high Core Action diversity.

The roughly even motion counts do not prove that the vote is strategic. The
current deterministic personas have no Realignment-specific conditional
weights, so the weighted backend treats the three motions alike and seeded
randomness supplies most variation. Human negotiation, misleading promises,
tile-specific incentives, and purposeful coalition voting remain untested.

The report repeats the earlier balance warnings: Imperial Research Lab leads
substantially, AGI remains almost absent, and objectives rarely complete.
These are investigation signals, not evidence that the map caused the spread.
This study has no unchanged thirteen-tile control group and is too small to
attribute differences from the first baseline to Realignment.

## Changes associated with the selected rule

These deltas were selected by the user and implemented before this simulation.
The simulation verified their integration; it did not choose them.

| Surface | Delta |
| --- | --- |
| Canonical rulebook | Replaced the incomplete thirteen-tile footprint with a radius-two nineteen-tile board; defined ring pools, movement distances, secret ballots, three motions, tie resolution, component movement, Transmission reconciliation, adjacency suspension, and Round IV timing. |
| Machine-readable game data | Expanded the location inventory to nineteen, added exact center/inner/outer placement counts, added three Realignment motion contracts, and added three ballots per faction. |
| Browser rules engine | Generates complete deterministic ring pools, rotates rings by identity, resolves hidden rival ballots, records receipts, and pauses round advancement until the active player votes. |
| Browser prototype | Renders the 3–4–5–4–3 board silhouette and provides the blind Realignment ballot surface with post-reveal counts. |
| Simulation environment | Bumped the complete environment to `selected-rules-v2`; added simultaneous policy-backed ballots, ring movement, event receipts, match aggregates, and adjacency checks for Mega-Clusters and agreements. |
| Strategy layer | Receives Realignment as an ordinary legal-decision packet. No persona-specific preference was selected. |
| Player references | Added the sixth round step and a dedicated Realignment reference card. |
| Content inventory | Updated map copies to nineteen and added eighteen physical ballot cards. |
| Manufacturing recommendation | Updated the advisory BOM and art exposure for nineteen tiles and eighteen ballots. |
| Playtest plan | Added movement, ring occupancy, ballot, adjacency, Transmission, suspension, and restoration observations. |
| Tests | Added full-ring geometry, deterministic placement, cross-ring adjacency change, blind tie-break, browser round gate, simulator vote count, and aggregate coverage. |

## Changes made because of this simulation

- No rule number, faction power, strategy weight, scoring value, objective,
  AGI requirement, map count, or motion changed after reading this report.
- No canonical surface was edited to hide or soften the balance warnings.
- This receipt was added so the raw result, validity boundary, and exact
  implementation surface remain reconstructable.

## Next controlled tests

1. Add candidate Realignment preferences to copied strategy profiles without
   changing the canonical profiles, then compare motion use and positional
   outcomes against this equal-preference baseline.
2. Record distance traveled, before/after adjacency, suspended projects, and
   restored contracts as aggregate metrics.
3. Run human four-player sessions focused on whether secret negotiation is
   legible, surprising, and fast enough.
4. Investigate faction spread, AGI drought, and objective drought as separate
   hypotheses rather than tuning them simultaneously with the map.
