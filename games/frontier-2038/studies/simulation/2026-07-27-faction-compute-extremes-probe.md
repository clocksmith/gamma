# Faction Compute-extremes probe

Date: 2026-07-27  
Evidence label: simulation  
Verdict: both one-Compute shifts move in the intended direction but are too
small to select

## Identity

- Raw local report:
  `20260727T234310710Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-faction-compute-extremes-v1-20260727-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `99977777d4f2d3b03a2db3c82e9163083211f97601554271fe27f2225a39c20a`
- Source commit:
  `400d564d0a6b775308fdd8e0be88cdebb8ac20c4`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `faction-compute-extremes-v1`
- Root seed: `m3t4-faction-compute-extremes-v1-20260727`
- Matches per arm: `3,976`
- Bounded adversarial matches: `70`
- Matched common-seed pairs per candidate: `3,976`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

## Results

Demis Hassabis at 2 starting Compute changed his aggregate paired win share by
`-1.582` percentage points and mean score by `-0.252`. Raw faction rates moved:

- two players: `67.84%` to `64.32%`;
- three players: `44.06%` to `42.81%`;
- four players: `36.04%` to `34.86%`; and
- five players: `25.64%` to `24.09%`.

Elon Musk at 4 starting Compute changed his aggregate paired win share by
`+1.849` percentage points and mean score by `+0.214`. Raw rates moved:

- two players: `39.45%` to `41.67%`;
- three players: `23.33%` to `26.56%`;
- four players: `16.99%` to `19.45%`; and
- six players: `8.83%` to `10.10%`.

Both directions are useful, but neither closes enough of the observed gap.
Their multiplicity-adjusted paired intervals also cross zero. Selecting these
values would add a rules revision while leaving the practical faction problem
largely intact.

## Decision

Do not select either one-Compute arm. Register a stronger symmetric probe:
Demis starts at 1 Compute and Elon starts at 5. Each remains an independent
one-lever comparison against canonical. If both are selected individually, a
combined confirmation is still required.

## Surface audit

- Canonical semantic graph and numeric values: unchanged.
- Rulebook, faction cards, reference aids, and browser prototype: unchanged.
- Simulation engine: retains the isolated starting-Compute levers.
- Tests: direct variant isolation remains covered.
- Playtest documentation: this receipt records the non-selection.
- Immutable release: none.
