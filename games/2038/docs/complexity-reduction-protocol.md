# Complexity-Reduction Candidate Protocol

This protocol governs proposed reductions to Mandate 2038’s mechanical density.
It protects the current Default Game while allowing narrative-rich alternatives
to be tested as isolated rules candidates.

## Authority and status

The canonical Default Game remains the `defaultGame` profile in
`content/data/game-config.json`. The three candidates in the Rule-Change Register
are proposed and inactive. They must not be added to `playRuleModules` or either
supported profile until they pass this protocol.

The source of status is `content/data/rule-change-register.json`; the generated
ledger is `dist/docs/rule-change-register.md`. Rationale belongs in this protocol
and `docs/design-decisions.md`; player-facing rules belong in `content/copy/` only
after a candidate is accepted.

## Candidate queue

| Candidate | Isolated change | Protected identity | Primary risk |
| --- | --- | --- | --- |
| [`single-generator-default`](../experimental/single-generator-default.md) | One Generator per player; remove source selectors and the second Generator | Energy geography, Power negotiation, Scrutiny, Grid-Ready AGI | Energy-site dominance or first-player advantage |
| `presence-only-politics` | Remove Influence cubes; use CEO, Team, and Facility presence for political access | Spatial politics, Trust, Scrutiny relief, Joint Ventures | Presence becomes a universal movement bonus and politics loses persistence |
| `two-program-factions` | One persistent identity and one signature program per faction | Six institutional identities and protected faction strengths | Factions become shallow or signature programs become compulsory |

The stored-token economy is a later queue, not part of these three tests. Do not
combine it with a candidate in the first evidence pass.

## Test sequence

1. **Freeze the baseline.** Record the executable version, rules fingerprint,
   profile, seed population, player counts, factions, seats, strategies, and
   backend regimes.
2. **Write the candidate contract.** Name the exact changed lever, unchanged
   rules, protected faction strengths, physical state, and legal-decision schema.
3. **Run integrity checks.** Verify finite nonnegative state, legal choices,
   action exhaustion, Production ordering, Audit behavior, scoring, AGI routes,
   and replay identity.
4. **Run isolated evidence.** Use common seeds and the existing unified frame at
   three, four, and five players. Rotate factions, Initiative seats, weighted
   and greedy policies, and backend regimes. Keep candidate and baseline paired.
5. **Run human evidence.** Measure setup handling, rules questions, state errors,
   perceived agency, negotiation quality, downtime, and recall of faction
   identity. Simulation cannot settle those questions.
6. **Record a disposition.** Mark the candidate accepted, rejected, or retained
   as a diagnostic. Acceptance requires a new synchronized rules candidate and
   updated physical, player-aid, browser, simulator, and test surfaces.

## Promotion gate

A candidate cannot advance because it is simpler or narratively elegant. It must
preserve procedural integrity, avoid a registered faction or seat dominance,
retain viable openings and winning paths, preserve meaningful negotiation, and
pass the three-, four-, and five-player gates. A candidate that passes alone may
enter one explicitly registered package-interaction test with an empty canonical
arm. Package evidence tests interaction; it cannot replace isolated evidence.

## Required receipt

Every study receipt must link the candidate ID, exact source commit, baseline and
candidate fingerprints, common-seed contract, player-count cells, policy/backend
regimes, raw reports, human-session records, disposition, and every surface that
would change on promotion. Narrative copy changes without a mechanical candidate
do not count as rules evidence.
