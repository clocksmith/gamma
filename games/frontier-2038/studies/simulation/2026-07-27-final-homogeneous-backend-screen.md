# Final homogeneous-backend balance screen

Date: 2026-07-27
Evidence label: simulation
Verdict: freeze the current rules; no registered exploit justifies another
numeric change

## Identity

- Raw local report:
  `20260727T194144827Z-unified-matrix-audit-0-7-1-c4b26a0f3867-m3t4-unified-backend-regimes-v3-20260727-11990x4-unified-matrix-cli.json`
- Report SHA-256:
  `3af800d70d3260eb97b38290566f83924cc1404bd0345551d3219adf810c9e3f`
- Source commit:
  `48726227fbe747764e94e748cdfc0250bb1c5563`
- Source dirty: `false`
- Executable: `0.7.1`
- Physical candidate: `0.4.0-rc.16-test`
- Engine: `selected-rules` `0.9.1`
- Ruleset fingerprint:
  `sha256:c4b26a0f3867f595a33ac8e83f951852b536d0114a0d46d47405205ded69a6ac`
- Preregistration: `unified-backend-regimes-v3`
- Root seed: `m3t4-unified-backend-regimes-v3-20260727`
- Matrix matches: `11,920`
- Bounded adversarial matches: `70`
- LLM calls: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`

The frame crossed player counts two through six, fixed and variable Mandates,
balanced faction and Initiative rotation, rotating windows of all seven
personas, and four backend regimes: all weighted, all greedy, and both
alternating patterns. Adaptive allocation used regime-specific seat, faction,
and strategy uncertainty.

## Registered result

- Status: `inconclusive_precision_not_reached`.
- Homogeneous-regime credible dominance cells: `0`.
- Homogeneous-regime credible head-to-head dominance cells: `0`.
- Credible three-persona meta cycles: `0`.
- Maximum core confidence-sequence half-width: `0.2681`.
- Pooled or mixed-regime diagnostic dominance cells: `3`.

The three diagnostic cells all combined Demis Hassabis with the Capability
Rusher at four, five, or six players. They remain visible because interaction
may matter, but they pool across opponent-backend regimes and cannot nominate a
physical rule change under the registered contract.

## Homogeneous-regime shape

At four players under all-greedy decisions, the top two personas were nearly
tied:

- Capability Rusher: `41.67%` raw win share across 336 appearances.
- Infrastructure Compounder: `41.56%` across 320 appearances.

At five players, the Capability Rusher led the all-greedy field at `37.24%`
across 392 appearances. At six players it led at `37.72%` across 464
appearances. Those are important diagnostic rates, but their multiplicity-safe
lower bounds did not clear the registered expected-win-plus-15-point rule.
They do not prove an unanswerable strategy.

Faction leaders also changed with backend regime:

- four-player all-greedy: Demis Hassabis, `36.78%`;
- four-player all-weighted: Dario Amodei, `36.51%`;
- five-player all-greedy: Jensen Huang, `37.08%`;
- five-player all-weighted: Demis Hassabis, `28.29%`;
- six-player all-greedy: Jensen Huang, `29.27%`; and
- six-player all-weighted: Demis Hassabis, `24.28%`.

No one faction led every homogeneous regime and player count. None cleared the
strict registered homogeneous dominance gate.

## Negotiation and ending

- Declarations: `15 / 11,920` (`0.126%`).
- Genuine AGI endings: `15 / 11,920` (`0.126%`).
- Declarations with a causally necessary supplier: `15`.
- Emergent cooperation rate: `29.60%`.
- Betrayal rate: `1.16%`.
- Causal supplier observations: `1,499`.
- Causal suppliers finishing in the top half: `56.97%`.
- Mean Audit hits per match: `13.70`.

Cooperative AGI remains rare but rules-legal, and a necessary supplier was
competitive more often than not in this deterministic sample. That is
feasibility evidence, not proof that human negotiation will feel fair.

## Decision

Do not change the rulebook again from this screen.

The corrected Foundry study already selected the per-four GPU divisor and
rejected the one-trigger Shovels probe. This canonical screen finds no
additional registered homogeneous exploit. A new change would therefore be
post-hoc tuning against a diagnostic maximum, violating the project’s own
promotion contract.

The current rules are frozen for controlled physical play. The next authority
must be observed table evidence about:

- whether Capability Rusher can be countered by human opponents;
- whether Demis Hassabis and Jensen Huang feel oppressive in the regimes where
  they lead;
- what suppliers demand for AGI-enabling Power;
- whether promises and betrayals feel voluntary rather than coerced;
- Realignment resolution time and drama;
- teachability, duration, emotional fairness, and memorable play.

## Surface audit

- Canonical rulebook: no change.
- Semantic game graph and numeric values: no change.
- Generated data and faction cards: no change.
- Simulation game engine: no rules change.
- Browser prototype, replays, and player aids: no change.
- Evidence runner: corrected regime allocation and gate are already committed.
- Automated tests: regime and gate contracts are covered.
- Physical playtest protocol: remains the next authority.
- Immutable game release: no new release; the physical rules remain
  `0.4.0-rc.16-test`.

This is bounded falsification evidence. It does not prove NP-hardness,
permanent balance, machine resistance, or fun.

## Post-screen synchronization

After this receipt froze the rules, executable `0.7.2`, engine `0.9.2`, and
physical candidate `0.4.0-rc.17-test` were issued to synchronize the corrected
homogeneous-backend harness and the bundled evidence documents without
rewriting the immutable `0.7.1` / rc.16 artifacts.

This follow-up changes no playable value. Every gameplay JSON file shared by
the `0.7.1` and `0.7.2` rulesets is byte-identical. The release additionally
corrects identity classification by moving descriptive
`data/simulation-copy.json` from the ruleset file set to the playtest-kit file
set. The resulting fingerprint rebaseline records a cleaner evidence boundary;
it does not retroactively alter this report or its exact source identity.
