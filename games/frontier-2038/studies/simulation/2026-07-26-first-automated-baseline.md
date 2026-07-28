# First Automated Four-Player Baseline

**Study ID:** `2026-07-26-first-automated-baseline`
**Evidence:** automated simulation, not a human playtest
**Generated:** July 26, 2026 at 13:03:25 UTC
**Raw local report:** `2026-07-26T130325Z-tournament-frontier-monte-carlo-100x4.json`
**SHA-256:** `f70604bb3df02ef7001d743e6648cb4eb77c1efe64ced95dfd5eb0bb1eeb72e4`

## Configuration

- 100 complete four-player matches.
- Seed: `frontier-monte-carlo`.
- Personas: Balanced Operator, Capability Rusher, Infrastructure Compounder,
  and Market Maximalist.
- Backends: seeded weighted policy for every seat; no Claude or Codex calls.
- Canonical provisional rules variant: Audit multiplier 1; Facility cost 2;
  Deploy cost 1 Compute; starting-grid Power 1; Customer scoring 2 Mandate;
  AGI requirements 9 Capability, 3 Customers, 3 Facilities, 2 Trust, and
  3 Compute.
- Three sampled replays were retained.

## Aggregate results

| Measure | Result |
| --- | ---: |
| Action diversity | 84.38% |
| Faction win-share range | 39.00 percentage points |
| Reported seat/profile range | 16.00 percentage points |
| AGI eligibility | 0.25% of player-matches |
| AGI declarations | 0 |
| Secret-objective completion | 8.75% |
| Mean Systemic Risk created | 0.79 per match |

### Factions

| Faction | Win share | Mean Mandate | Capability | Customers | Facilities | Audit hits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Imperial Research Lab | 49% | 21.72 | 8.53 | 2.27 | 1.22 | 3.32 |
| Platform Empire | 28% | 19.50 | 6.65 | 2.44 | 1.32 | 3.26 |
| Coalition Lab | 13% | 17.57 | 6.02 | 1.68 | 1.43 | 3.22 |
| Vertical Empire | 10% | 16.30 | 6.34 | 1.75 | 1.29 | 3.83 |

### Personas

| Persona | Reported win share | Mean Mandate | Capability | Customers | Facilities |
| --- | ---: | ---: | ---: | ---: | ---: |
| Capability Rusher | 35% | 19.60 | 7.65 | 2.37 | 0.84 |
| Market Maximalist | 27% | 19.82 | 7.71 | 2.77 | 1.06 |
| Balanced Operator | 19% | 18.47 | 6.40 | 1.89 | 1.35 |
| Infrastructure Compounder | 19% | 17.20 | 5.78 | 1.11 | 2.01 |

## Interpretation

The Core Action economy did not collapse: all six actions remained active and
overall action diversity was high. The more urgent problems are downstream.
The AGI climax essentially never occurred, and secret objectives resolved in
fewer than one in ten player-matches. Reorganization, Open Weights, and
Narrative Capture were much more accessible than Mega-Clusters or any AGI
declaration.

Faction rotation makes the faction result meaningful enough to investigate:
Imperial Research Lab led Vertical Empire by 39 win-share points and 5.42 mean
Mandate. Imperial also reached 8.53 mean Capability, while Vertical suffered
the most Audit hits. This is a strong imbalance signal, not yet a selected
nerf or buff.

The persona ranking is not independently valid. In this report, factions
rotated but personas stayed fixed to seats. Persona and seat effects are
therefore confounded. The reported seat-bias alert must not be interpreted as
pure positional bias.

## Changes made because of this study

| Surface | Delta |
| --- | --- |
| Canonical rulebook | No rule change. The study does not yet justify selecting a balance variant. |
| Machine-readable game data | No faction, action, scoring, objective, or AGI values changed. |
| Simulation runtime | Personas now rotate independently from factions across seats; faction rotation uses a separate schedule. |
| Aggregate report contract | Seat summaries retain every encountered persona ID instead of claiming one fixed persona. |
| Browser Simulation Lab | Results now separate faction, persona, and seat aggregates; seat cards disclose rotation; future reports show their automatic local archive path. |
| Report persistence | Every completed browser job is automatically written to `studies/simulation/`. |
| Rule/reference surfaces | No player-facing rule or reference-card change because no physical rule changed. |
| Tests | Added independent-rotation and automatic-archive coverage. |
| Playtest documentation | Added the required simulation-to-change receipt and surface-audit protocol. |

## Next controlled experiments

1. Re-run the unchanged baseline after independent persona rotation, using a
   run count divisible by the sixteen faction/persona pairings.
2. Confirm whether Imperial dominance and Vertical weakness survive that
   correction.
3. Search AGI and objective accessibility separately from faction balance.
4. Present candidate deltas for user selection before changing canonical game
   rules.
