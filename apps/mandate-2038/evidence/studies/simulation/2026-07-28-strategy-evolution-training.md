# Weak-persona strategy evolution training

Date: 2026-07-28  
Evidence label: simulation training  
Verdict: two inspectable champions nominated for a fresh-seed matrix holdout;
training fitness is not balance evidence

## Identity

Both jobs used executable `0.7.3`, engine `selected-rules` `0.9.5`, four
players, six generations, eight candidates per generation, 24 runs per seat,
weighted deterministic decisions, and no LLM calls.

### Trust Governor

- Raw local report: `20260728-trust-governor-evolution-v1.json`
- SHA-256:
  `e38c79765596975b4292709b7c18611ffb763b6e448efc022ea1db7480c67f1a`
- Source commit:
  `5d197f2c222411ba1a9485c55f353710ec7ada7f`
- Source dirty: `false`
- Seed: `m3t4-trust-governor-evolution-v1-20260728`

The best observed generation reached `25.52%` training win share; the final
champion reached `23.44%`, up from a first-generation baseline observation of
`14.58%`. Its largest strategic changes increase Research, Mega-Cluster,
Narrative Capture, Agent Swarm, and Fusion interest while reducing its
overweight AGI declaration and Open Weights preferences.

### Power Broker

- Raw local report: `20260728-power-broker-evolution-v1.json`
- SHA-256:
  `bf8aeed7533c9d249979b386ce80d021507e7264647ea43e749b7806fa13f6fa`
- Source commit:
  `5d197f2c222411ba1a9485c55f353710ec7ada7f`
- Source dirty: `false`
- Seed: `m3t4-power-broker-evolution-v1-20260728`

The final champion reached `29.17%` training win share, compared with
`26.04%` in the first generation. It remains infrastructure-oriented but adds
Research, Influence, Narrative Capture, and Agent Swarm while becoming less
eager to accept every Power sale.

## Interpretation

The weak personas can become materially more competitive without changing a
physical rule, but the optimizer repeatedly evaluated candidates on related
training rosters. These values may be noise or overfitting. Neither profile is
promoted into canonical authored strategy data.

The next registered test replaces only these two profiles with their generated
champions and evaluates the complete unified matrix on a new root seed. The
report must retain profile fingerprints and provenance so it cannot be
mistaken for the canonical policy ecology.

## Surface audit

- Physical rules and semantic game graph: unchanged.
- Canonical player strategies: unchanged.
- Evolution reports: local raw evidence, referenced by hash.
- Unified matrix runner: gains explicit, fingerprinted profile overrides.
- Browser and rulebook: unchanged.
- Immutable release: none.
