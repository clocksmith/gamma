# Foundry Shovels executable correction

Date: 2026-07-27  
Evidence label: executable-integrity correction  
Decision: withdraw Foundry balance conclusions produced before the corrected
Shovels trigger; rerun all final Foundry probes

## Broken boundary

The physical faction rule says:

> When another player spends at least two Compute in one action, gain one
> Runway, at most twice per round.

Executable `0.7.0` checked that trigger only at the end of ordinary Core Action
resolution. Core Research and Deploy normally spend one Compute. The relevant
two-or-more-Compute payments occur in Wild Actions, including a solo
Mega-Cluster and Declare AGI, so the simulator did not award the defining
Foundry royalty for those actions.

The error was exposed by the preregistered Shovels-cap probe: its canonical
two-trigger arm and one-trigger arm produced byte-for-byte-equivalent outcomes
across all 3,964 matched common-seed pairs.

## Invalid diagnostic identity

The report is
`20260727T184108697Z-unified-matrix-audit-0-7-0-45278b2ce910-m3t4-foundry-shovels-final-20260727-7998x4-unified-matrix-cli.json`.

- SHA-256:
  `b121bc4aef7353f32603e14bf82227ca66882d6c88a2d4026ab0dc16d9f328f9`
- Source commit: `cd7fe61da1520177bf7801e409f669ec93ddb919`
- Source dirty: `false`
- Executable: `0.7.0`
- Matrix matches: 7,928 plus 70 bounded adversarial matches
- Matched common-seed pairs: 3,964
- Standing mismatches: 0
- Integrity violations reported by the old invariant set: 0
- Paired Foundry win-share delta: exactly `0`
- Paired Foundry score delta: exactly `0`

The zero integrity count does not rescue the balance result: the invariant set
did not yet test that a qualifying Wild Action triggered Shovels.

## Correction

Executable `0.7.1` observes the acting institution’s Compute immediately before
and after the entire selected action. It applies Shovels once when a Core,
Wild, or Faction Action spends at least two Compute. Agent Swarm is treated as
one selected Wild Action, so two one-Compute Core resolutions inside it can
collectively trigger the royalty. Immediate trades remain outside the action
spend and cannot trigger Shovels.

A regression resolves a solo Mega-Cluster against a rival Foundry and verifies:

- two Compute are spent;
- one Runway is awarded;
- Shovels income is logged; and
- the per-round cap prevents a second award.

## Evidence disposition

The earlier GPU, starting-Compute, New Architecture, canonical `0.7.0`, and
all-greedy `0.7.0` balance reports remain reproducible descriptions of their
exact executable. They are not evidence for the synchronized physical game
because that executable omitted a faction benefit.

The corrected three-arm study is complete. It retains Everybody Gets a GPU at
one Mandate per four rivals and retains the two-trigger Shovels cap. Its
replacement authority is
[`2026-07-27-corrected-foundry-final-selection.md`](2026-07-27-corrected-foundry-final-selection.md).
