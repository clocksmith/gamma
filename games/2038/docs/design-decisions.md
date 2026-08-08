# Mandate 2038 Design Decisions

**Rules reference:** `0.6.0-rc.2-test`
**Status:** current rationale and implementation-boundary ledger

This document explains why the selected game has its present shape. It does
not repeat card text or resolve play: [`core-rules.md`](core-rules.md) is the
only authority for the physical game.

The former complexity-proposal document was folded into this ledger after its
five selected proposals were implemented. Earlier 19-tile, every-Era
Realignment, Transmission, Tactic, secret-objective, and endgame-scoring
assumptions are historical only.

## Product identity

Mandate 2038 is a competitive institutional strategy game that also produces a
shared future. Its durable pillars are:

- six Core Actions with only three selections each Era;
- simultaneous commitment followed by spatial resolution;
- a modular hex economy without combat or elimination;
- push-your-luck Research;
- asymmetric institutions;
- negotiated infrastructure and public risk;
- four Eras that escalate from credible controversy to solemn absurdity;
- optional AGI rather than compulsory graduation; and
- separate institutional and civilizational outcomes.

New systems are frozen until the controlled four-player test supplies evidence.

### Supported player counts

The selected product permits two through six players and suggests three, four,
and five. Four players is
the authoritative balance configuration because it preserves negotiation,
spatial competition, and clean parity while keeping sequential resolution
bounded. Three and five players remain complete games, not variants: every
selected four-player change must be rerun at both counts and rejected if it
creates a credible integrity, faction, seat, strategy, negotiation, or
congestion regression. Two and six players are playable exploratory
configurations, but their reports are non-promotional diagnostics until they
receive their own evidence contract.

## Selected complexity contract

### Select → Move → Act

Every ordinary turn uses one visible grammar. Cost, destination, mode, risk,
and exhaustion belong on the Action surface. Readying changes a future choice;
it does not create an immediate action. Agent Swarm is the only compound-action
exception.

This preserves difficult opportunity costs while reducing procedural lookup.
The challenge should come from choosing among scarce capabilities, not from
discovering a new resolution sequence on every card.

### One visible exception per authority layer

An ordinary action may combine its printed rule, one destination bonus, one
faction modifier, and applicable global state. Persistent Headlines use
physical reminders. Every exception has a timing window. A current Headline
overrides an older global effect only when both alter the same field.

Tactics remain a deferred module because the baseline already contains enough
variation to test the central engine.

### Eras teach the game

- **Progress:** movement, Core Actions, Research, Facilities, Customers, and
  Scrutiny.
- **Capacity:** Generators, Networks, Links, and early Escalations.
- **Authority:** persistent agreements, Government votes, and competing
  public realities.
- **Continuity:** Agent Swarm, Fusion, AGI, and the civilizational ending.

Later systems remain visible from setup, but the Era card is the sole unlock
authority.

### Mandate stays public

Customers, Capability thresholds, Trust thresholds, Era Mandates, Fusion,
faction awards, and AGI score when they occur. Facilities and control create
position and production rather than receiving automatic endgame points. Final
calculation contains only the offline penalty before resolving the shared
ending.

This makes negotiation legible and lets every simulated score change retain a
specific source.

## Selected spatial contract

The game uses thirteen tiles:

- Frontier at the center with no Facility spaces;
- six shuffled operational-ring tiles; and
- six shuffled public-ring tiles in a sixfold-symmetric footprint.

Every non-Frontier tile has two Facility spaces. The smaller board restores
scarcity while keeping all action categories reachable.

Each player has one Infrastructure Network. Adjacency and two Link tokens
govern both Power delivery and the Network bonus. There is no separate
Transmission graph.

Networks and the starting-grid marker exist from setup. Generators, Links,
Mega-Clusters, and the Network production bonus unlock in Era II.

Default Game keeps the randomized jurisdiction fixed for all four Eras.
Jurisdictional Realignment is preserved as part of the single bundled Advanced
Play profile: its blind vote rotates a physical ring while every site-bound
component travels with its district. Players then receive all three Era IV
actions to respond. There is no postgame rotation.

Fusion deliberately occupies one of the Grid tile’s three Generator slots.
Filling those slots can deny Fusion; the first controlled test must measure
whether that creates meaningful spatial competition or an accidental lockout.

## Selected interaction contract

In Default Game, one immediate resource trade may occur during any player’s
resolution: a complete named offer is accepted or rejected. Each player may
make one Production Power purchase request. Advanced Play is one bundled
profile, but its constituent changes are separately identified in the
rule-change register below. Counteroffers and third-party claims are distinct:
a counteroffer can be accepted or rejected by the original offer maker; claims
let other eligible players compete for that published counteroffer.
Influence is required for persistent Joint Ventures and Trust manipulation.
Power is bought immediately during Production from a consenting adjacent
Network; no Power contract persists.

Influence cubes can be relocated, so political control never becomes
permanently solved when a supply empties. Joint Ventures use numbered neutral
host pairs. Their identities survive Realignment; their operation still
depends on the printed range and connectivity requirements.

Promises about later turns are not binding. The game supports negotiation
without requiring a general contract-enforcement system.

## Rule-change register

The generated [rule-change register](../dist/docs/rule-change-register.md)
is the single status record for Default/Advanced changes. Its structured
source records each change’s decision, implementation state, dependencies, and
module IDs. It does not authorize players to assemble ad hoc profiles: Default
Game and Advanced Play remain the only supported profiles until a new profile
is deliberately selected and validated.

## Selected risk and ending contract

Audit draws scale by player count. Scrutiny beyond a player’s ten physical
cubes immediately becomes a Runway-or-Trust penalty. Era IV Audit converts
risk into Runway or Mandate loss so late exposure remains consequential.

Declare AGI requires Capability nine, three Customers, three Facilities with
Grid-Ready markers, Trust two, and three Compute. Markers record successful
operation during a completed Production, replacing the declaration-time
capacity proof. It scores but does not end play. The Blog Post Headline lowers
only the Capability requirement.

The winner is the institution with the most Mandate. AGI emergence and
Open/Closed continuity are independent tests. A normal-threshold declarer
establishes emergence. The ending is Open only when collective Trust improves
beyond setup by the player count and unresolved Systemic Risk remains below the
player count; otherwise it is Closed. Winning and building the preferable
future are deliberately different achievements.

## Selected content boundary

Dovetalis Labs, Loopfold AI, Mirevanta Works, Kestralyn, Orisonix, and
Corthaven are the canonical fictional institutions. Stable institutional IDs
remain internal compatibility keys for simulations, saved games, and balance
evidence; they are not player-facing aliases.

The institutions and their CEOs are fictional. They must not imply endorsement
or turn a Headline into a factual accusation. Commercial publication remains a
separate decision requiring appropriate legal review.

The tone is solemn institutional absurdity. Early controversies must have
credible benefits and harms. Later effects may become polarized and alarming,
but the dystopia must emerge from defensible local decisions.

Rules titles, display titles, rules text, flavor, and art direction remain
separate fields. Flavor never creates a mechanic.

## Baseline exclusions

The following material exists as design inventory but is not part of the
controlled `0.6.0-rc.2-test` test:

- Tactic cards;
- secret objectives;
- Specialist and Patron cards;
- final art and production layouts; and
- autonomous promotion of optimizer output into canonical rules.

Evidence from a run that includes an excluded module must name that variant.

## Implementation status

Executable game `0.9.1` implements `0.6.0-rc.2-test` under engine
coverage `three-to-five-profiles-v1`. Grid-Ready markers are earned by demonstrated
Production and invalidated by movement, disconnection, or later
insufficient Power. Browser-native deterministic play, server-backed LLM play,
replay, policies, and Monte Carlo share that contract.

Synchronization is implementation proof, not balance proof. Structured
balance numbers remain hypotheses until a tracked study receipt replaces their
provenance.

The `0.9.1` / `0.6.0-rc.2-test` advancement changes no physical rule. It
corrects the executable selection contract so every unused Core Action and
every unlocked, unspent Escalation remains legally selectable even when it has
no current resolution. Resolution metadata lets deterministic policies avoid
known dead choices without deleting them. A blocked selection exhausts, and a
blocked Escalation spends its token, exactly as the physical commitment rule
requires. Because legal decision packets and deterministic sampling change,
earlier simulation remains historical evidence rather than balance authority
for this executable.

The `0.9.0` / `0.6.0-rc.1-test` advancement creates a new Default Game:
one-offer immediate trades, one Production Power request per player, and no
Era III Realignment. Advanced Play restores all three former procedures as
one profile. This is a mechanical revision requiring new three-, four-, and
five-player evidence; `0.8.35` and earlier reports remain historical
full-rules evidence and do not qualify the new Default Game.

The `0.8.34` / `0.5.0-rc.34-test` advancement changes no legal action, cost,
resource value, Mandate award, faction ability, setup, or end condition. It
adds simulation-only Deal Flow conversion attribution and a fingerprinted
deterministic Coalition policy treatment for a preregistered diagnostic. The
physical-candidate suffix advances only to preserve immutable synchronized
release identity; it is not a balance-rule revision.

`0.5.0-rc.20-test` selected the clarification that ring rotation is district
movement rather than Facility relocation for Grid-Ready purposes, the
two-source Power inventory, and the evidence-selected rule that Everybody Gets
a GPU scores one Mandate per four rivals. It promotes four controlled
conversion changes from the winning-path tolerance confirmation: Demis scores
less public Mandate at Capability nine and twelve except for five-player
Capability twelve; Elon scores one Mandate only when Industrial Velocity
actually reduces a completed Facility’s cost; Jensen’s New Architecture
self-Compute follows accepted licenses with no automatic base; and Customers
four and five score one Mandate each while retaining full income. Every other
numerical rule is frozen pending human evidence.
Grid-Ready cooperation remains deliberately frozen for the controlled physical
test. Realignment is retained only in Advanced Play pending comparative human
evidence.

`0.5.0-rc.21-test` changes no playable rule from rc.20. Executable `0.8.20`
adds complete realized-value telemetry for Emergency Pause, Audited Deployment,
and Responsible Scaling. The corrected fresh-seed faction swaps reject a
universal Dario nerf or Sam buff because the Dario effect reverses by backend
and negotiation-aware Sam is approximately neutral against Mark.

`0.5.0-rc.22-test` changes no playable rule from rc.21. Executable `0.8.21`
adds per-opponent persona/backend selection to interactive play and an
origin-restricted, token-paired localhost bridge for the deployed browser.
Every LLM opponent receives an independent bounded decision budget and
deterministic fallback. This is runtime access and policy configuration, not a
board-game mechanics or balance change.

`0.5.0-rc.23-test` changes no playable rule from rc.22. Executable `0.8.22`
corrects the deployed Simulation Lab’s player-count DOM binding discovered by
the live HTTPS-to-localhost browser check.

`0.5.0-rc.24-test` changes no playable rule from rc.23. Executable `0.8.23`
makes weighted and greedy interactive opponents execute directly in the
browser. The token-paired localhost bridge remains optional and is selected
only for Claude, Codex, hybrid opponents, or server-backed Simulation Lab
jobs. The browser imports the same match, decision, persona, and deterministic
policy modules as the Node executable; this is a deployment/runtime correction,
not a board-game mechanics or balance change.

The rc.17 physical candidate has no mechanics delta from rc.16. It exists
because the synchronized evidence documents and executable harness changed;
the immutable rc.16 bundle and every report attributed to executable `0.7.1`
remain historical evidence.

The rc.18 candidate likewise changes no playable physical rule from rc.17. It
synchronizes the fresh-seed-validated Trust Governor and Power Broker profiles
with executable `0.7.4`, giving subsequent faction probes a clean,
reconstructable evidence identity.

The rc.19 candidate changes no playable physical rule from rc.18. Executable
`0.7.5` adds the staged AGI funnel, realized faction-ability values,
player-count-specific outcome summaries, and preregistered common-seed faction
swaps. These are evidence instruments, not rule changes.

The `0.5.0-rc.24-test` candidate and executable `0.8.23` retain the three- to
five-player product boundary, make four players the balance authority, and
require three/five regression coverage. Their playable mechanics are identical
to rc.20 and executable `0.8.19`.

Executable `0.8.22` also preserves identity classification:
`dist/runtime/simulation-copy.json` is evidence-boundary copy, not a playable rules
input. It now contributes to the playtest-kit fingerprint instead of the
ruleset and mechanics fingerprints. The new fingerprint is therefore a
deliberate identity rebaseline, not evidence of a gameplay delta.

## Unified evidence-frame decision

Automated evidence is one sampled seven-factor frame rather than separately
labeled “diverse” and “cooperative” batches. Cooperation is classified after a
match from promises, betrayals, trades, causal Power support, and supplier
placement. Sparse cells are shrunk before interpretation, while a
multiplicity-safe bounded confidence sequence supplies the conservative
threshold gate.

Adaptive allocation may choose where to sample next, but it cannot change the
registered outcome, threshold, or interpretation boundary. Best-response
mutation is a diagnostic slice, never a balance authority. Claude or Codex
appears only in a committed, explicitly authorized, decision-capped holdout;
fresh calls test robustness and read-only cached calls test reproducibility.
Strict provider schemas require every declared output field while nullable
commentary fields remain semantically optional. Failed calls retain attempted
provider provenance through deterministic fallback. Fresh capture uses
write-only cache mode so it cannot silently reuse an old answer; the paired
replay uses read-only mode and fails on any missing decision.

## Open evidence questions

Measure before changing numbers:

- Can unfamiliar four-player groups complete the game from the rulebook?
- Does the thirteen-tile map create useful scarcity without compulsory routes?
- Does Default Game preserve enough adaptation without Realignment, and does
  bundled Advanced Play justify its additional interruption?
- Are non-declaration strategies competitive?
- Does emergency generation dominate after its actual Audit cost is attributed?
- Does Loopfold AI lead after each Production?
- Does Mirevanta Works or Research-campus protection flatten Research risk?
- Do all three Grid Generator slots fill before Era IV?
- Is Influence selected for genuine political choices rather than efficient
  Trust scoring?
- Are Reorganization and Open Weights credible alternatives to their competing
  Escalations?
- Does the Future Timeline produce a memorable history?

Four players is the authoritative balance target. Three- and five-player
quality, deferred modules, and numerical balance remain open until controlled
evidence exists. Three and five are the suggested full formats and mandatory
regression guards for any selected four-player change. Two and six players are
playable exploratory configurations, not current balance-authority formats.

The deterministic
[`lean balance and cooperative-AGI study`](../evidence/studies/simulation/2026-07-26-lean-balance-and-cooperative-agi.md)
observed rare rules-legal cooperative declarations and narrowed two large
faction outliers. Its schema-v3 supplier attribution was not causal and is
withdrawn; only clean schema-v4 runs may support supplier-viability claims.
Simulation still cannot settle human negotiation, teachability, or duration;
those remain physical-test questions.
