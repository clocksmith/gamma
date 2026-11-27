# Simulation and player strategies

The current engine is `lab/environment/selected-rules-match.js`. Browser, server, and simulation callers use it; `core-economy-match.js` reexports that engine. `web/src/engine.js` contains deterministic RNG, deck, and pure Training utilities, without a second gameplay implementation.

The engine models eighteen Action hexes around an Era center, one-edge Org movement, Org equipment, five holding tracks, Reputation Review, push-your-luck Research, immediate Headlines, faction abilities, and fixed-rate consented trades. Turns resolve sequentially: optional trade, one Org stays or moves one edge, then its destination Action is performed or deliberately skipped. A skip is legal even when the Action is affordable; movement, equipment, presence and ordinary Production remain while Action costs, rewards and Action-specific abilities do not apply. Off-map entry and Organize’s second-Org reassignment preserve their existing rules. One objective from each Era packet is revealed at setup before the first Headline. All four remain visible without later redraws and score once from final holdings at game end. The separate World Ending uses recognition and average final Reputation. Historical diagnostic fields never influence scoring. Existing strategy weights are unqualified starting policies for this redesigned game; earlier balance findings do not transfer.

Run `npm run simulate:monte-carlo -- --help` for the active CLI. `createSimulation()` accepts explicit seeds, player count, profiles, deterministic backends, kit assignments, and record/replay configuration. Four players is the primary balance configuration; three and five need separate evidence and two remains exploratory. Six-player requests are rejected. Rich and batch projections preserve mechanical outcomes.

Current reports use schema eight and replay schema four. Historical report viewing preserves original Trust, scores, objectives, and replay identity without rescoring. Kit fallback is display-only. Historical hex geometry is available only for old report display, outside the public playable dependency list.

Policies retain their action weights during this migration. Conditions referring to removed Power, project, and risk quantities are retired rather than assigned fabricated values. Old geography and multi-project study treatments are incompatible; their original scripts and receipts remain historical. Numeric search may vary bounded current rules only; it cannot restore old systems. It produces candidates and never edits authored rules automatically.

Decision packets enumerate legal choices and public state, including all four setup objectives, while withholding hidden draw order and unrevealed cards. Deliberate destination skips are legal positional choices, not known-unresolvable Action attempts or forced no-ops. Trade responders see the proposed immediate exchange. Rejection or provider failure clears pending terms. Trades accept only one-for-one quantities and validate both payments and caps atomically.

Claude/Codex policies use the shared decision contract and require explicit LLM authorization. This redesign's acceptance uses deterministic policies only and makes no remote-provider performance claim.

Retain raw simulation reports in the local ignored studies archive and tracked dated receipts with seed, configuration, source/fingerprint identity, hashes, and limits. Automated consistency is distinct from numerical balance and human physical play. Old spatial and balance receipts qualify their frozen releases only. No current redesign number inherits their promotion status.

The historical 0.24.4 policy correction filtered known unresolvable Action
selections when an executable choice existed; a positive weight penalty had
previously still sampled them. The 2026-10-12 candidate must preserve deliberate
skips as executable positional choices rather than discard movement because its
destination Action is unaffordable. Research availability, preview and debit use
the same declared two-Compute cost; bounded `researchComputeCost` overlays remain
internal simulation parameters. The
[economy study](../evidence/studies/2026-10-11-economy-results.md) compares costs
with identical corrected policies rather than crediting the bot fix to one arm.
