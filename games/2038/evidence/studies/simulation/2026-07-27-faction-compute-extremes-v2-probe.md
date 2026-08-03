# Faction Compute-extremes v2 probe

Date: 2026-07-27  
Evidence label: simulation  
Verdict: stronger starting-Compute changes are directional but still do not
resolve the faction extremes

## Identity

- Raw local report:
  `20260727T235529669Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-faction-compute-extremes-v2-20260727-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `eed5555a70bbe48420b0d27198152c96016573c9d762de61cd7e454858e8a221`
- Source commit:
  `8ca32f5d15cb9d2ffab618852823fdf17d89a2b5`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `faction-compute-extremes-v2`
- Root seed: `m3t4-faction-compute-extremes-v2-20260727`
- Matches per arm: `3,976`
- Bounded adversarial matches: `70`
- Matched common-seed pairs per candidate: `3,976`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

## Results

Demis Hassabis at 1 starting Compute changed his aggregate paired win share by
`-4.154` percentage points and mean score by `-0.673`. Raw faction win rates
moved from:

- `62.63%` to `60.26%` at two players;
- `46.56%` to `42.08%` at three;
- `35.94%` to `32.13%` at four;
- `26.55%` to `22.99%` at five; and
- `20.22%` to `14.56%` at six.

Elon Musk at 5 starting Compute changed his aggregate paired win share by
`+3.964` percentage points and mean score by `+0.511`. Raw rates moved from:

- `42.76%` to `48.16%` at two players;
- `23.33%` to `29.27%` at three;
- `14.96%` to `19.19%` at four;
- `11.75%` to `14.16%` at five; and
- `6.99%` to `9.93%` at six.

The direction is useful, but the residual shape is wrong. Demis remains high
at low counts and becomes slightly low at six; Elon approaches parity at two
but remains materially low as the table grows. The multiplicity-adjusted
paired intervals also cross zero. Starting Compute is therefore not a
sufficient final balance instrument.

The canonical arm recorded a `0.361%` forced-no-op rate, five AGI declarations
in 3,976 matches, zero integrity violations, and no policy fallbacks. The full
matrix gate remained `inconclusive_precision_not_reached`; this receipt records
practical direction, not a release-grade balance claim.

## Decision

Do not select either starting-Compute value as the final correction. Preserve
the isolated variant levers for reproducibility. Probe the mechanics that
actually scale:

- cap Demis Hassabis's Scientific Method across the game rather than subtracting
  another generic resource;
- let Elon Musk's Industrial Velocity apply to infrastructure choices as well
  as Facilities;
- test Sam Altman's weak engine with additional starting Runway; and
- reduce Jensen Huang's high-count passive Shovels income.

Each remains an independent one-lever common-seed comparison.

## Surface audit

- Canonical semantic graph and numeric values: unchanged.
- Rulebook, faction cards, reference aids, and browser prototype: unchanged.
- Simulation engine: retains the isolated starting-Compute levers.
- Tests: variant isolation remains covered.
- Playtest documentation: this receipt records non-selection and the next
  registered question.
- Immutable release: none.
