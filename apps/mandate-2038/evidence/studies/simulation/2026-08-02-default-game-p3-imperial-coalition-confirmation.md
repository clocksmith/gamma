# Default Game three-player Imperial–Coalition confirmation

**Date:** 2026-08-02  
**Evidence label:** Simulation / deterministic paired faction isolation  
**Status:** Valid completed confirmation. It rejects a policy-independent
Imperial Research Lab-over-Coalition Lab explanation in this field. No rule
candidate and no canonical rule change follow.

## Registered execution

- Preregistration:
  `default-game-p3-imperial-coalition-confirmation-v2`, committed before
  execution at `cb99f8479d0d6de304ff9beaddc0e638b2470f4a`.
- Exact frozen source: `cb99f8479d0d6de304ff9beaddc0e638b2470f4a`,
  `sourceDirty: false`.
- Executable game `0.9.0`, release status `playtest`, physical rules candidate
  `0.6.0-rc.1-test`, and Default Game profile
  (`playProfileId: default-game`).
- Ruleset fingerprint:
  `sha256:90b3727be120e24656c1a56b3ee9f4762e5b0433593ed7971cb8aa4aa973ae7b`.
- Engine: selected-rules `0.11.0`, fingerprint
  `sha256:fd77c01848f3ed0e92ea433bb34b7128e771392eed0afa67ac94646719af29dc`.
- Root seed:
  `frontier-2038-default-game-p3-imperial-coalition-confirmation-v2-20260802`.
- The study scheduled and completed 7,200 deterministic matches: 3,600 exact
  common-seed pairs. Each pair changed only the focal institution between
  Imperial Research Lab (left) and Coalition Lab (right).
- The field crossed all six eligible two-faction opponent rosters from
  Platform Empire, Vertical Empire, Safety Laboratory, and Foundry; all three
  focal seats; and homogeneous `weighted` and `greedy` deterministic policy
  fields. Every seat used `balanced_operator`; Mandates remained variable.
- Batch projection used eight outer worker threads and one simulator worker
  per arm. There were zero LLM calls, zero quarantined matches, and stable
  comparison → arm → match ordering.
- Raw local report:
  `evidence/studies/simulation/2026-08-02-default-game-p3-imperial-coalition-confirmation-v2.raw.json`.
  Immutable local archive:
  `evidence/studies/simulation/20260803T010709296Z-balance-audit-0-9-0-90b3727be120-frontier-2038-default-game-p3-imperial-coalition-confirmation-v2-7200x3-faction-swap-cli.json`.
  Both bytes have SHA-256
  `917299542abe6bb6c17cba68269f8350cb64ada7c54c306914d2c76874035136`.

## Frozen primary analysis

The preregistered unit is the exact common-seed focal pair. Positive values
favour Imperial Research Lab. Two-sided 98% Student-t intervals are calculated
over paired game outcomes. The aggregate meets both registered precision
targets; the policy families retain their separately reported precision.

| Field | Pairs | Imperial minus Coalition Mandate | 98% interval | Win credit | 98% interval | Rank advantage | 98% interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All registered fields | 3,600 | +0.268 | [+0.102, +0.434] | -0.024 | [-0.046, -0.002] | -0.036 | [-0.075, +0.003] |
| Weighted policy | 1,800 | +1.137 | [+0.836, +1.437] | +0.047 | [+0.014, +0.081] | +0.127 | [+0.069, +0.184] |
| Greedy policy | 1,800 | -0.601 | [-0.725, -0.476] | -0.095 | [-0.122, -0.067] | -0.198 | [-0.249, -0.147] |

The 98% Mandate half-width is `0.166` overall, `0.300` for weighted, and
`0.125` for greedy. The corresponding win-credit half-widths are `0.022`,
`0.033`, and `0.027`; the aggregate and greedy fields satisfy the registered
`<= 0.03` target, while weighted is recorded as a precise directional family
but does not independently clear that narrower secondary bound.

Every registered opponent roster was included. Seat families were modest and
not coherent as a general correction signal: aggregate Imperial-minus-Coalition
Mandate was `+0.253`, `+0.348`, and `+0.203` at seats zero, one, and two,
respectively; win credit was `-0.020`, `-0.005`, and `-0.046`.

## Verdict and limits

The policy families reverse direction across Mandate, win credit, and rank.
Weighted policy favours Imperial Research Lab; greedy policy favours Coalition
Lab. This satisfies the preregistered falsification condition for a broad,
policy-independent Imperial-over-Coalition rule hypothesis. The small pooled
Mandate average is not a faction correction signal because the registered
homogeneous fields disagree materially.

This does **not** establish that three-player Default Game is balanced. It
examines only one focal faction pair, one deterministic profile family, and
variable Mandates; it cannot prove human negotiation quality or four- and
five-player safety. There were zero legal AGI declaration windows and zero
declarations in all 3,600 paired outcomes, so AGI-route balance remains
unmeasured.

The remaining three-player warning is therefore best described as a
deterministic policy–faction interaction to improve or broaden in the
evaluation harness, not evidence that either faction's physical rules should
change. A physical candidate still requires a separately preregistered
one-lever 3/4/5-player common-seed audit, fresh seeds, and explicit human
approval.

## Affected-surface audit

- Canonical rulebook, game data, browser, simulator, reference cards, and
  player aids: no mechanical or copy change from this study.
- Tests: no gameplay implementation changed; the clean source passed
  `npm run content:validate` and `npm run content:check` before execution.
- Historical pre-Default and LLM evidence: preserved as separate context and
  not pooled with this field.
- Balance status: Default Game has stronger evidence against the specific
  Imperial-versus-Coalition main-effect hypothesis, but no balance claim or
  completion claim is authorized.
