# Foundry multiplayer-scaling rule selection

Date: 2026-07-27  
Evidence label: preregistered unified simulation matrix  
Decision: Everybody Gets a GPU scores one Mandate per four rivals; New
Architecture and starting Compute remain unchanged

> **Withdrawn as current balance authority.** Executable `0.7.0` did not apply
> the Shovels royalty to qualifying Wild Actions. This receipt remains an exact
> history of that executable, but it cannot support the synchronized physical
> game. See
> `2026-07-27-foundry-shovels-executable-correction.md`.

## Hypothesis and frame

The registered file
`studies/simulation/preregistrations/foundry-multiplayer-scaling-probes.json`
compared one canonical arm with two independent one-lever arms:

- Everybody Gets a GPU: one Mandate per two rivals → one per four;
- New Architecture: three Compute → two.

The unified frame sampled player counts 2–6, balanced faction and Initiative
rotation, all seven authored personas, fixed and variable Mandates, weighted
and greedy decision backends, and explicit seeded randomness. Cooperation,
Power trades, promises, betrayal, causal supplier support, and supplier
competitiveness were outcomes, not assigned cohorts. No LLM caller was used.

## Evidence identity

The valid confirmation report is
`20260727T181929266Z-unified-matrix-audit-0-6-7-74e48d44072f-m3t4-foundry-scaling-confirmation-20260727-11998x4-unified-matrix-cli.json`.

- SHA-256:
  `853be69d542b41eb97380e2229a55cf1a546cef60e4e6525feab58aafeaecb84`
- Source commit: `51240df89eb0885ae2b33a0fe406d407b58e29d2`
- Source dirty: `false`
- Executable: `0.6.7`
- Engine: `selected-rules` `0.8.7`
- Matrix matches: 11,928, or 3,976 per arm
- Bounded adversarial matches: 70
- Matched common-seed pairs per candidate: 3,976
- Unmatched pairs: 0
- Standing mismatches: 0
- Integrity violations: 0

The earlier 3,598-match report
`20260727T175238107Z-unified-matrix-audit-0-6-6-376586876c40-m3t4-foundry-scaling-probes-20260727-3598x4-unified-matrix-cli.json`
had the same direction but insufficient precision. The first 11,998-match
attempt is invalid because it found a rule-independent negative final score;
its disposition and repair are recorded in
`2026-07-27-current-matrix-and-mega-cluster-integrity.md`.

## Results

Relative to canonical, the GPU-per-four arm changed Foundry:

- paired win share: `-0.067014`;
- multiplicity-adjusted bounded interval: `[-0.129773, -0.004255]`;
- mean final score: `-0.879267`;
- greedy-backend win share: `-0.093275`;
- weighted-backend win share: `-0.041071`.

Canonical Foundry raw win share was `39.57%`, `38.07%`, and `37.11%` at four,
five, and six players. GPU-per-four reduced those to `32.97%`, `30.79%`, and
`29.02%`. It did not change the two-player rule, where neither divisor awards
Mandate. The canonical arm produced a credible six-player
Foundry×greedy dominance cell. The GPU-per-four arm did not.

New Architecture at two Compute changed Foundry paired win share by only
`-0.011678`, with bounded interval `[-0.074437, 0.051081]`, and mean score by
`-0.104923`. It did not remove the credible six-player Foundry×greedy cell.
That lever is rejected.

All arms produced 10 AGI declarations in 3,976 games (`0.2515%`). Emergent
cooperation was `35.09%`; betrayal was `1.18%`; causal supplier competitive
rates were `53.31%` canonical and `53.47%` GPU-per-four. The scoring lever did
not alter AGI feasibility or negotiation frequency in the paired sample.

The report still says `credible_dominance_detected` because its joint verdict
correctly includes the canonical and rejected Architecture arms. This does not
describe the selected GPU-per-four arm.

## Selection and limits

The user authorized one final evidence-backed tuning pass. The per-four rule is
selected because it targets the observed player-count scaling, has a paired
effect interval below zero, removes the registered credible interaction from
its own arm, and leaves the faction’s thematic table-wide dividend intact.

This is bounded machine evidence, not proof of mathematical hardness, human
balance, fun, or permanent exploit resistance. Physical tests remain the
authority for deal quality, perceived fairness, Realignment, duration, and
whether the reduced reward still feels consequential.

## Surface audit

- Canonical rulebook: Foundry Round IV text changes from per two rivals to per
  four; final Mandate floor remains explicit.
- Semantic graph: shared Foundry divisor changes `2 → 4`; all player text
  continues to render from that value.
- Machine-readable data: regenerated.
- Simulator and browser engine: canonical rules variant reads the new graph
  value; no hard-coded duplicate changes.
- Browser prototype and gallery: regenerated text shows per four rivals.
- Reference/player aids: no separate Foundry number exists; no change.
- Tests: canonical/probe expectations inverted and full contracts rerun.
- Playtest documentation: records the selected lever, evidence identity, and
  remaining human questions.
- Numeric provenance: the canonical shared-variable pointer cites this receipt.
- Physical components and artwork: no quantity or art-direction change.
- Report and decision schemas: no change.
- LLM caller contracts and holdout: no change and no calls made.
- Immutable releases: executable `0.7.0`, engine `0.9.0`, and synchronized
  physical candidate `0.4.0-rc.15-test`.
