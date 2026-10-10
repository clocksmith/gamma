# Current-state Era objective comparison

Registered before comparison results on 2026-10-09. This is a scoring-package
candidate study, not balance promotion or observed human play. No policy tuning.

Baseline: frozen Gamma `daf5bbd14`, executable 0.21.7, rules rc.13 (equipment only).
Candidate: executable 0.22.1, rules rc.15. The sole mechanical treatment is the
eight redesigned Era Mandates. Starts, costs, actions, Audit, policies and
production definitions remain fixed. Trust milestones and AGI awards remain.

## Registered blocks

Four players are primary: six focal factions × four focal seats × two unchanged
backends (weighted and greedy) × three Mandate deck rotations = 144 pairs.
Three- and five-player guardrails: six factions × one focal seat × two backends
× three rotations = 36 pairs each. Total: 216 matched pairs, 432 complete games.
Seeds are `current-era-{players}-{faction}-{seat}-{backend}-{rotation}`.
Focal faction occupies the focal seat; subsequent seats take successive factions
in canonical order. Profiles rotate with seat and faction identically in both
arms. Distinct kit IDs follow seat order. Public negotiation is enabled.

Each Era deck is ordered by authored card order and rotated by the registered
rotation before play. This exposes all twelve cards evenly without changing the
random-number stream. Both arms receive identical card IDs and Headlines.
The frozen baseline runs its own original evaluator; it is never reinterpreted
under candidate definitions. Capture qualification, metric value and points at
each arm's post-Audit scoring point, including zero and no-qualifier outcomes.

## Measures and validity

Retain raw paired outcomes in the local simulation archive and hash them in a
tracked dated receipt. Report per-card qualification, no-qualifier frequency,
point contribution, and faction/seat allocations. Compare total scores, paired
score deltas, faction wins by seat, current Runway, Customer levels, repeated
Customer-objective winners, Venture activity, and winning-path labels.
Inspect resource hoarding and starting advantages descriptively. Do not infer
causality for isolated starting values or policy-optimal strategies from a
whole-package comparison. Any follow-up starting-value experiment is separate.

Completion, determinism, read-only evaluation and history independence are
engineering acceptance. They do not establish strategic balance. Small guardrail
cells and unchanged policies limit inference; all new thresholds remain
hypotheses. Also run the unified audit frame with maximum 480 games, two initial runs per cell, batch size two, canonical rules, counts 3/4/5, both Mandate modes, all registered strategy/backend regimes, and the bounded adversarial slice; retain its coverage and
non-promotion verdict. Never attach old balance receipts to new scoring rules.
Human ownership recognition and scoring without turn-history questions require
an actual physical session; generated-master checks cannot substitute for it.
