# Corrected Foundry final-selection receipt

Date: 2026-07-27  
Evidence label: simulation  
Verdict: retain one Mandate per four rivals and two Shovels triggers per round

## Identity

- Raw local report:
  `20260727T185945836Z-unified-matrix-audit-0-7-1-c4b26a0f3867-m3t4-foundry-corrected-final-20260727-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `07bc0bb9857fa39c2c7ccc0d3839e5452d11c50da4882f1b0de0f383cef08fbb`
- Source commit:
  `1f20193b389bc2625656d88cc532fc8eca0bdc4f`
- Source dirty: `false`
- Executable game: `0.7.1`
- Physical candidate: `0.4.0-rc.16-test`
- Engine: `selected-rules` `0.9.1`
- Ruleset fingerprint:
  `sha256:c4b26a0f3867f595a33ac8e83f951852b536d0114a0d46d47405205ded69a6ac`
- Preregistration:
  `foundry-corrected-final-probes`
- Root seed:
  `m3t4-foundry-corrected-final-20260727`
- LLM calls: `0`

The job executed 11,928 deterministic matrix matches plus 70 bounded
adversarial-diagnostic matches. Each of the three rules arms received 3,976
common-seed matches across player counts two through six, fixed and variable
Mandates, faction and seat rotations, all authored personas, and weighted and
greedy decision backends.

## Registered arms

1. `canonical`: Everybody Gets a GPU scores one Mandate per four rivals;
   Shovels may trigger twice per round.
2. `foundry_gpu_two_rivals`: change only the GPU divisor from four to two.
3. `foundry_shovels_once_per_round`: change only the Shovels cap from two to
   one.

The executable correction in
[`2026-07-27-foundry-shovels-executable-correction.md`](2026-07-27-foundry-shovels-executable-correction.md)
was active in every arm. Integrity violations and policy fallbacks were zero.
All 3,976 pairs matched in each comparison, with zero standing mismatches.

## Results

### Everybody Gets a GPU

Changing the divisor from four rivals to two:

- increased Foundry win share by `6.094` percentage points;
- increased Foundry mean score by `0.870`;
- increased Foundry×greedy win share by `8.626` percentage points; and
- produced a credible six-player Foundry×greedy cell: raw win share `53.75%`,
  posterior interval `49.22%–57.87%`, versus an expected `16.67%`.

The multiplicity-bounded paired interval remained wide and crossed zero, so it
does not establish the exact size of the effect. Its direction, score effect,
and independently credible candidate-arm cell all reject restoring the more
generous divisor. The canonical divisor of four remains selected.

### Shovels

Reducing the corrected Shovels cap from two triggers to one:

- changed aggregate Foundry win share by exactly `0.000` percentage points;
- changed Foundry mean score by `-0.0018`;
- changed Foundry×greedy win share and score by exactly zero; and
- changed one forced no-op and two Mandate-threshold events across 3,976
  matches without changing standings.

The second trigger is rarely relevant under the current action economy, but
removing it supplies no demonstrated balance benefit. The cap of two remains.

## Other findings

- Canonical declarations: `7 / 3,976` matches (`0.176%`).
- Every canonical declaration had a causally necessary Power supplier.
- Canonical emergent-cooperation rate: `34.38%`.
- Canonical betrayal rate: `1.03%`.
- Causal suppliers finishing in the top half: `55.38%` across 576 supplier
  observations.
- The registered audit still reports credible dominance for the
  six-player `capability_rusher × greedy` cell. This is not a Foundry lever:
  the same cell appears under all three rules arms. Mixed-backend games also
  make the greedy policy substantially stronger than the deliberately
  stochastic weighted policy. That finding motivates backend-regime
  stratification, not an unregistered scoring rewrite.

## Decision and surface audit

- Canonical numeric graph: no rule change.
- Rulebook and faction card: no change; the current divisor and cap are
  retained.
- Generated data, player aids, gallery, and browser prototype: no content
  change.
- Simulation engine: no post-result rules change.
- Simulation evidence design: homogeneous all-weighted and all-greedy fields
  are added beside both alternating patterns so strategy strength can be
  separated from opponent-backend quality.
- Tests: backend-regime coverage and pairwise-stratum assertions are added.
- Physical-test protocol: no change.
- Immutable game release: no new rules release is required for a rejected
  probe.

This receipt supersedes the withdrawn Foundry selection conclusion based on
the defective `0.7.0` executable. It does not claim that Foundry, any persona,
or the complete game is balanced. Physical play remains authoritative for
negotiation quality, perceived fairness, Realignment, duration, and fun.
