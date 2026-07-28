# Backend-regime v2 allocation correction

Date: 2026-07-27  
Evidence label: simulation-harness validity  
Decision: do not use the v2 matrix to change rules; correct allocation and gate
semantics, then rerun

## Identity

- Raw local report:
  `20260727T192803769Z-unified-matrix-audit-0-7-1-c4b26a0f3867-m3t4-unified-backend-regimes-v2-20260727-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `bd03d4d72bf5cc46556c0bc22184fc413e6b67335bafc78e3dfa6a51539f8e9a`
- Source commit:
  `ec776a632d1eae96f8a62d865ccec7209a3daba0`
- Source dirty: `false`
- Executable: `0.7.1`
- Ruleset fingerprint:
  `sha256:c4b26a0f3867f595a33ac8e83f951852b536d0114a0d46d47405205ded69a6ac`
- Preregistration: `unified-backend-regimes-v2`
- Root seed: `m3t4-unified-backend-regimes-v2-20260727`
- Matrix matches: `11,928`
- Bounded adversarial matches: `70`
- LLM calls: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`

## Finding

The report correctly created all-weighted, all-greedy, and both alternating
backend regimes. Initial coverage was balanced. Adaptive allocation, however,
still scored uncertainty in the older pooled `strategy` and `backend`
families. It did not score `strategyBackendRegime` or
`factionBackendRegime` uncertainty. Later batches therefore concentrated in
mixed cells while homogeneous cells remained shallow.

At four through six players, homogeneous strategy exposures were only
`96–192` and homogeneous faction exposures were only `112–224`, despite the
11,928-match total. The multiplicity-safe confidence sequences remained too
wide for the intended homogeneous comparison.

The headline gate also treated pooled and alternating-regime dominance as a
rules failure. Its credible cells were driven by pooled faction/strategy
interactions and mixed regimes, including
`alternating_greedy_first`. No regime-specific homogeneous cell cleared the
registered rule threshold and confidence sequence together.

## Valid descriptive results

The report remains a reproducible description of its exact sampler:

- declarations: `18 / 11,928` (`0.151%`);
- Genuine AGI endings: `17 / 11,928` (`0.143%`);
- all declarations had a causally necessary supplier;
- emergent cooperation: `35.30%`;
- betrayal: `1.17%`;
- suppliers finishing in the top half: `56.10%` across 1,870 observations;
- mean Audit hits: `15.11`; and
- no credible meta cycle under the strict registered gate.

These values do not repair the allocation mismatch and do not authorize a
rules change.

## Correction

The v3 runner:

1. adds backend regime to seat-level inference;
2. allocates batches using regime-specific faction and strategy uncertainty;
3. uses homogeneous-regime seat, faction, strategy, interaction, and pairwise
   cells for the rules gate; and
4. publishes pooled and alternating-regime dominance separately as diagnostic
   evidence.

This changes evidence interpretation, not game mechanics. The canonical
rulebook, semantic game graph, generated data, prototype, player aids, physical
test protocol, and immutable game release require no change.
