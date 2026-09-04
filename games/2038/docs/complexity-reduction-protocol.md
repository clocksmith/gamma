# Complexity-Reduction Candidate Protocol

This protocol governs future reductions to Mandate 2038’s mechanical density.
It preserves a named current baseline while allowing alternatives to be tested
as isolated rules candidates.

## Authority and status

The canonical Default Game remains the `defaultGame` profile in
`components/game.json`. Accepted baseline simplifications are not
optional rule modules. A future candidate must be registered as proposed and
remain outside `playRuleModules` and both supported profiles until selected.

The source of status is `components/rule-changes.json`; the generated
ledger is `dist/docs/rule-change-register.md`. Rationale belongs in this protocol
and `docs/design-decisions.md`; player-facing rules belong in `rules.md` and `components/`
after a candidate is accepted.

## Current simplified baseline

| Accepted decision | Canonical change | Protected identity | Remaining evidence question |
| --- | --- | --- | --- |
| `single-generator-default` | One location-defined Generator per player | Energy geography, Power negotiation, Scrutiny, and a visible retained allocation snapshot | Energy-site dominance or Initiative advantage |
| `equal-presence-control` | CEO, Team, and Facility each contribute one presence; ties control nothing | Spatial politics, Trust, Scrutiny relief, Joint Ventures | Politics loses persistence or movement becomes universally optimal |
| `shared-program-display` | Six public Program cards and two markers per player replace private copies and a track | Public escalation, timing pressure, and once-per-game choices | Programs become scripted or insufficiently contested |
| `research-protection-refresh` | Research Protection refreshes each Era and Research visits protect only that run | Push-your-luck identity without a second spendable currency | Research becomes too safe or protection feels forgettable |
| `deterministic-dossier` | Supported evidence and printed claim strength replace bag draws and comeback arithmetic | Secret commitments, uncertainty, evidence, and a dramatic endgame claim | Resolution becomes predictable too early |
| `nineteen-hex-board` | One center, six inner, and twelve outer tiles form a complete radius-two board | Geographic specialization, movement, control, and Realignment | Added space weakens interaction or increases setup burden |
| `simplified-profile-boundary` | Default is the teachable core; Advanced adds six distinct experiences | One coherent baseline and one coherent expansion | Advanced setup cost exceeds its added strategic value |

Selection authorizes implementation, not a balance claim. The original
single-Generator candidate and its receipts remain in `experimental/` and
`evidence/` as historical provenance; the canonical contract now lives in
`components/game.json` and player-facing rules.

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
