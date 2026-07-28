# M3T4 2038 Design Decisions

**Rules reference:** `0.5.0-rc.9-test`
**Status:** current rationale and implementation-boundary ledger

This document explains why the selected game has its present shape. It does
not repeat card text or resolve play: [`core-rules.md`](core-rules.md) is the
only authority for the physical game.

The former complexity-proposal document was folded into this ledger after its
five selected proposals were implemented. Earlier 19-tile, every-round
Realignment, Transmission, Tactic, secret-objective, and endgame-scoring
assumptions are historical only.

## Product identity

M3T4 is a competitive institutional strategy game that also produces a
shared future. Its durable pillars are:

- six Core Actions with only three selections each round;
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

The selected product supports three, four, and five players. Four players is
the authoritative balance configuration because it preserves negotiation,
spatial competition, and clean parity while keeping sequential resolution
bounded. Three and five players remain complete games, not variants: every
selected four-player change must be rerun at both counts and rejected if it
creates a credible integrity, faction, seat, strategy, negotiation, or
congestion regression. Two and six players remain readable as historical
simulation cohorts but are not supported by this rules candidate.

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

- **The Demo:** movement, Core Actions, Research, Facilities, Customers, and
  Scrutiny.
- **The Scale:** Generators, Networks, Links, and early Wild Actions.
- **The Narrative:** persistent agreements, Government votes, and competing
  public realities.
- **The Claim:** Agent Swarm, Fusion, AGI, and the civilizational ending.

Later systems remain visible from setup, but the Era card is the sole unlock
authority.

### Mandate stays public

Customers, Capability thresholds, Trust thresholds, Round Mandates, Fusion,
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
Mega-Clusters, and the Network production bonus unlock in Round II.

Jurisdictional Realignment occurs once, after Round III Mandate scoring. The
blind vote rotates a physical ring while every site-bound component travels
with its district. Players then receive all three Round IV actions to respond.
There is no postgame rotation.

Fusion deliberately occupies one of the Grid tile’s three Generator slots.
Filling those slots can deny Fusion; the first controlled test must measure
whether that creates meaningful spatial competition or an accidental lockout.

## Selected interaction contract

One immediate resource trade may occur during any player’s resolution.
Influence is required for persistent Joint Ventures and Trust manipulation.
Power is bought immediately during Production from a consenting adjacent
Network; no Power contract persists.

Influence cubes can be relocated, so political control never becomes
permanently solved when a supply empties. Joint Ventures use numbered neutral
host pairs. Their identities survive Realignment; their operation still
depends on the printed range and connectivity requirements.

Promises about later turns are not binding. The game supports negotiation
without requiring a general contract-enforcement system.

## Selected risk and ending contract

Audit draws scale by player count. Scrutiny beyond a player’s ten physical
cubes immediately becomes a Runway-or-Trust penalty. Round IV Audit converts
risk into Runway or Mandate loss so late exposure remains consequential.

Declare AGI requires Capability nine, three Customers, three Facilities with
Grid-Ready markers, Trust two, and three Compute. Markers record successful
operation during a completed Production, replacing the declaration-time
capacity proof. It scores but does not end play. The Blog Post Headline lowers
only the Capability requirement.

The winner is the institution with the most Mandate. The world reaches Genuine
AGI only when a normal-threshold declarer exists, collective Trust improves
beyond setup, and unresolved Systemic Risk remains bounded. Otherwise it enters
the Closed Loop. Winning and building the preferable future are deliberately
different achievements.

## Selected content boundary

Sam Altman, Mark Zuckerberg, Demis Hassabis, Elon Musk, Dario Amodei, and
Jensen Huang are the canonical identities for the named parody prototype.
Stable institutional IDs remain internal compatibility keys for simulations,
saved games, and balance evidence; they are not player-facing aliases.

The portrayals are fictional satire based on public institutional roles. They
must not imply endorsement or turn a Headline into a factual accusation.
Commercial publication remains a separate decision requiring appropriate
legal review.

The tone is solemn institutional absurdity. Early controversies must have
credible benefits and harms. Later effects may become polarized and alarming,
but the dystopia must emerge from defensible local decisions.

Rules titles, display titles, rules text, flavor, and art direction remain
separate fields. Flavor never creates a mechanic.

## Baseline exclusions

The following material exists as design inventory but is not part of the
controlled `0.5.0-rc.9-test` test:

- Tactic cards;
- secret objectives;
- Specialist and Patron cards;
- final art and production layouts; and
- autonomous promotion of optimizer output into canonical rules.

Evidence from a run that includes an excluded module must name that variant.

## Implementation status

Executable game `0.8.8` implements `0.5.0-rc.9-test` under engine
coverage `three-to-five-grid-ready-v1`. Grid-Ready markers are earned by demonstrated
Production and invalidated by movement, disconnection, or later
insufficient Power. Browser play, replay, policies, and Monte Carlo now share
that contract.

Synchronization is implementation proof, not balance proof. Structured
balance numbers remain hypotheses until a tracked study receipt replaces their
provenance.

`0.5.0-rc.9-test` retains the clarification that ring rotation is district
movement rather than Facility relocation for Grid-Ready purposes, the
two-source Power inventory, and the evidence-selected rule that Everybody Gets
a GPU scores one Mandate per four rivals. Its only playable delta from rc.19
is the supported player range and its balance authority: three to five
players, designed at four and guarded at three and five. Corrected common-seed
evidence retained the GPU divisor: restoring the more generous per-two value
increased Foundry results and created a credible historical six-player
Foundry×greedy cell. The Shovels cap remains two; a one-trigger probe changed
no standings and did not justify a rules change.
Grid-Ready cooperation and mandatory Round III Realignment remain deliberately
frozen for the controlled physical test.

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

The `0.5.0-rc.9-test` candidate and executable `0.8.8` select the three- to
five-player product boundary, make four players the balance authority, and
require three/five regression coverage. No faction, resource, action,
Headline, Power, Grid-Ready, Realignment, scoring, or ending value changes.

Executable `0.8.8` also preserves identity classification:
`data/simulation-copy.json` is evidence-boundary copy, not a playable rules
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
- Does Realignment create adaptation without erasing infrastructure planning?
- Are non-declaration strategies competitive?
- Does emergency generation dominate after its actual Audit cost is attributed?
- Does Mark Zuckerberg lead after each Production?
- Does Demis Hassabis or Research-campus protection flatten Research risk?
- Do all three Grid Generator slots fill before Round IV?
- Is Influence selected for genuine political choices rather than efficient
  Trust scoring?
- Are Reorganization and Open Weights credible alternatives to their competing
  Wild Actions?
- Does the Future Timeline produce a memorable history?

Four players is the authoritative balance target. Three- and five-player
quality, deferred modules, and numerical balance remain open until controlled
evidence exists. Three and five are full supported formats and mandatory
regression guards for any selected four-player change. Two and six players
remain historical study configurations, not current product formats.

The deterministic
[`lean balance and cooperative-AGI study`](../studies/simulation/2026-07-26-lean-balance-and-cooperative-agi.md)
observed rare rules-legal cooperative declarations and narrowed two large
faction outliers. Its schema-v3 supplier attribution was not causal and is
withdrawn; only clean schema-v4 runs may support supplier-viability claims.
Simulation still cannot settle human negotiation, teachability, or duration;
those remain physical-test questions.
