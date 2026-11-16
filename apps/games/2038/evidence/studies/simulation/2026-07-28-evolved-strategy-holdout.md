# Evolved-strategy fresh-seed holdout

Date: 2026-07-28  
Evidence label: simulation holdout  
Verdict: promote the evolved Trust Governor and Power Broker profiles as
stronger deterministic test opponents; do not change a physical rule from this
study

## Identity

- Raw local report:
  `20260728T004338707Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-evolved-strategy-holdout-v1-20260728-11990x4-unified-matrix-cli.json`
- Report SHA-256:
  `8e5f46e2e6c00bd24477114f6750485ae9b2e2d59fbf1a0c802023c4889cfc38`
- Source commit:
  `c338509a623d5c996aa73540ef1697606a2b1d40`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `evolved-strategy-holdout-v1`
- Root seed: `m3t4-evolved-strategy-holdout-v1-20260728`
- Matrix matches: `11,920`
- Bounded adversarial matches: `70`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

Both profile overrides are fingerprinted in the raw report and carry their
evolution provenance. The physical rules are canonical and unchanged.

## Results

At four players, fresh-seed raw win shares changed relative to the prior
authored-policy screen:

- Trust Governor: `14.06% → 25.31%`;
- Power Broker: `19.41% → 23.46%`;
- Capability Rusher: `40.03% → 38.17%`;
- Infrastructure Compounder: `29.85% → 27.80%`.

Trust Governor also reached `34.00%`, `22.64%`, and `17.05%` at three, five,
and six players. Power Broker reached `35.65%`, `19.10%`, and `14.47%`.
Neither champion became a persistent leader across table sizes.

Capability Rusher remained practically strong at four through six players
(`38.17%`, `29.77%`, and `28.58%`), but the registered audit found:

- zero credible homogeneous dominance cells;
- zero credible pairwise dominance cells;
- zero diagnostic dominance cells;
- zero credible three-profile meta cycles; and
- a `0.375%` forced-no-op rate, below the `3%` validity ceiling.

The matrix produced nine declarations in 11,920 games. The balance gate
remained `inconclusive_precision_not_reached`; these profiles improve policy
quality but do not prove game balance.

## Decision

Promote the two champion weight maps into the canonical deterministic persona
definitions. Their names, themes, goals, conditional rules, and physical game
surfaces do not change. This is an evidence-harness improvement: future
rule probes should face stronger Trust and Power strategies rather than weak
straw opponents.

No physical rule is selected here. Faction spread remains a separate concern:
Demis Hassabis and Jensen Huang still lead several player-count cells, while
Sam Altman and Elon Musk remain low at larger tables. Any correction must be
tested against the promoted policy ecology.

## Surface audit

- Canonical deterministic profiles: Trust Governor and Power Broker weights
  updated to their fingerprinted champions.
- Semantic graph and generated `data/player-strategies.json`: synchronized.
- Unified matrix: accepts and fingerprints profile overrides for future
  holdouts.
- Physical rulebook, cards, components, and browser game mechanics: unchanged.
- Executable and engine identity: incremented because policy evidence and
  matrix provenance changed.
- Immutable release: required before the promoted profiles become a clean
  evidence baseline.
