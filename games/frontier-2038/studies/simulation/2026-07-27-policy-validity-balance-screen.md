# Policy-validity balance screen

Date: 2026-07-27  
Evidence label: simulation  
Verdict: the corrected policy screen nominates a one-lever late-Capability
Mandate probe; it does not itself change the rules

## Identity

- Raw local report:
  `20260727T204648612Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-policy-validity-balance-v1-20260727-11990x4-unified-matrix-cli.json`
- Report SHA-256:
  `e27509565858e23a28536feb8058e5be71f205c36797535be32c00c927dba3e0`
- Source commit:
  `cd3df870b311843c655f892ff962bcd43a5dd800`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `policy-validity-balance-v1`
- Root seed: `m3t4-policy-validity-balance-v1-20260727`
- Matrix matches: `11,920`
- Bounded adversarial matches: `70`
- LLM calls: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`

The frame crossed player counts two through six, fixed and variable Mandates,
balanced faction and Initiative rotation, all seven authored personas, and
homogeneous and alternating weighted/greedy backends.

## Validity correction

Earlier deterministic cohorts selected known-unresolvable actions often enough
to contaminate balance interpretation: `16.09%` of action opportunities in a
1,200-game greedy cohort and `12.43%` in a weighted cohort became forced
no-ops. The corrected policies retain every legal Action choice but assign
known-dead selections a small nonzero weight. The corrected unified screen
recorded `1,938` forced no-ops across all player action opportunities, a rate
of `0.347%`, below the preregistered `3%` validity ceiling.

The opening-action metric was also repaired before this report. Ordinary
successful Round I actions are now recorded exactly once. Earlier reports
remain historical artifacts but are superseded for balance selection wherever
they relied on the contaminated action or opening evidence.

## Results

The conservative registered gate remained
`inconclusive_precision_not_reached`: no homogeneous cell cleared both its
partially pooled interval and its multiplicity-safe confidence sequence.
That prevents an automated balance claim, but it does not make the practical
rates acceptable design targets.

Across backends, the Capability Rusher won:

- `40.03%` at four players, versus `25%` expected;
- `31.22%` at five players, versus `20%` expected; and
- `31.24%` at six players, versus `16.67%` expected.

At four players it won `44.89%` in homogeneous-greedy games and `37.64%` in
homogeneous-weighted games. The Infrastructure Compounder also reached
`40.63%` at four players under homogeneous greedy play.

Faction effects were also uneven. Demis Hassabis won `34.73%` at four players,
while Elon Musk won `15.95%`. Across smaller counts Demis reached `65.01%` at
two and `49.07%` at three players. Jensen Huang rose to `29.68%` at five and
`24.91%` at six players.

The screen recorded `24` declarations (`0.201%`), all with a causally necessary
Power supplier. Suppliers placed in the competitive half `56.42%` of the time.
That remains feasibility evidence, not proof that human bargains feel fair.

## Decision and hypothesis

The corrected evidence rejects another rules freeze. It nominates exactly one
common-seed probe: leave Capability 3 and 6 worth 2 Mandate, but make Capability
9 and 12 worth 1 Mandate each. This preserves the early Research engine and
AGI requirement while removing at most 2 late points from the lane most
strongly associated with the observed practical advantage.

No faction value changes are bundled into this probe. If the scoring lever
reduces Demis and Capability Rusher together, it is the more general repair.
If it merely transfers dominance to infrastructure, Customers, Jensen, or
another faction, it must be rejected or followed by a separately registered
lever.

## Surface audit

- Canonical semantic graph and numeric values: no change from this screen.
- Canonical rulebook and physical cards: no change from this screen.
- Simulator: policy-validity and opening-evidence corrections are active;
  one experimental late-Capability scoring lever is added for the paired probe.
- Browser prototype and player aids: no canonical change.
- Tests: action viability, opening evidence, and the experimental scoring lever
  have direct regression coverage.
- Playtest protocol: no change; physical play remains the authority for
  counterplay, negotiation, duration, fairness, and fun.
- Immutable release: no release from this nomination alone.

This receipt does not claim mathematical NP-hardness, permanent balance, or
machine resistance.
