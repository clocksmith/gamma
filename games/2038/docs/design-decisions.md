# Mandate 2038 Design Decisions

**Rules reference:** `0.8.0-rc.19-test`
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
- **Capacity:** Generators and early Programs. Advanced Play also introduces
  Networks and Links.
- **Authority:** persistent agreements and competing public realities.
  Advanced Play also introduces Government votes and persistent Headline
  procedures.
- **Continuity:** Agent Swarm, Fusion, AGI, and the civilizational ending.

Later systems remain visible from setup, but the Current Era panel is the sole unlock
authority.

### Presentation cannot create a new phase

The current player board may group End-of-Era Resolution into four visual
bands—**Power** for Generate, Trade, and Allocate; **Economy** for Produce and
Partner; **Dossier** for the simultaneous secret filing; and **Consequences**
for Audit and Mandate. This is a presentation
hypothesis, not a rules change. Production remains the five numbered boxes,
followed by the separate Audit and Mandate phases. Human testing must justify
the visual grouping before it becomes a selected component layout.

### Mandate stays public

Customers, Capability thresholds, Trust thresholds, Era Mandates, Fusion, and
faction awards score when they occur. Facilities and control create
position and production rather than receiving automatic endgame points. Final
calculation applies the offline penalty, names the provisional Mandate winner,
and then resolves supported Dossier claims deterministically.

This makes negotiation legible and lets every simulated score change retain a
specific source.

## Selected spatial contract

The game uses nineteen tiles in a complete radius-two hexagon:

- Frontier at the center with no Facility spaces;
- six shuffled inner-ring tiles; and
- twelve shuffled outer-ring tiles.

The inner ring contains Research, Cloud, Foundry, Capital, Talent, and Grid.
The outer ring contains two each of Research, Cloud, Consumer, Media,
Government, and Renewable. Every non-Frontier tile has two Facility spaces.
The complete ring preserves exact sixfold geometry, removes empty perimeter
positions, and keeps every action category reachable.

Power delivery is profile-specific. Default Game uses local Power: a Generator
can power its owner's Facilities on its own hex or an adjacent hex. Advanced
Play gives each player one Infrastructure Network; adjacency and two Link
tokens govern pooled Power delivery. There is no Network production bonus or
separate Transmission graph.

The integrated starting-grid identity exists from setup. Generators and
Mega-Clusters unlock in Era II. Links and binary Network connectivity are
Advanced Play additions that also unlock in Era II.

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

Influence is an action, not a component supply. The acting CEO or Team must end
at Media, Government, or Capital to change Trust or Scrutiny. Political control
counts CEOs as two presence and Teams and Facilities as one; ties remain
uncontrolled. A Joint Venture must be proposed or terminated by an acting piece
at one of the player’s Facilities. Joint Ventures use numbered neutral host
pairs. Their identities survive Realignment; operation still depends on printed
range, Power, and connectivity.

Promises about later turns are not binding. The game supports negotiation
without requiring a general contract-enforcement system.

## Rule-change register

The generated [rule-change register](../dist/docs/rule-change-register.md)
is the single status record for Default/Advanced changes. Its structured
source records each change’s decision, implementation state, dependencies, and
module IDs. It does not authorize players to assemble ad hoc profiles: Default
Game and Advanced Play remain the only supported profiles until a new profile
is deliberately selected and validated.

Future complexity reductions are governed by the
[`complexity-reduction-protocol.md`](complexity-reduction-protocol.md). The
August 2026 simplification package is current: one location-defined Generator,
presence-only politics, two programs per Faction, removal of seven stored-token
families, and a stricter Default/Advanced boundary. These are baseline rules,
not optional modules, so they do not appear in either profile’s module list.
The register records them as accepted current decisions.

## Selected risk and ending contract

Audit draws scale by player count. Scrutiny beyond a player’s ten physical
cubes immediately becomes a Runway-or-Trust penalty. Era IV Audit converts
risk into Runway or Mandate loss so late exposure remains consequential.

AGI is a hidden four-Era Dossier rather than an Action or deterministic
declaration. After each Production, every player secretly files Commit or
Hedge for that Era. In Era IV all cards are revealed: every Commit costs one
Compute and adds one Scrutiny before the final Audit; Publication must be
committed and the full cost paid for a claim to be eligible.

The ordinary final-scoring winner, including the printed tie breakers, is the
provisional winner. The Audit bag is then rebuilt with all eighteen black
no-AGI cubes plus each eligible claim's faction-coloured prediction tokens.
Two cubes are drawn without replacement. Matching faction colours form AGI
and make that claimant the sole winner; every other pair preserves the
Mandate result. Claim tokens come from committed Dossier modules, Capability
thresholds, and a bounded Mandate-rank comeback bonus. This produces zero or
one declaration without a die, app, published percentage, or player-authored
arithmetic. The ending is
Open only when collective Trust improves
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
controlled `0.8.0-rc.19-test` test:

- Tactic cards;
- secret objectives;
- Specialist and Patron cards;
- final art and production layouts; and
- autonomous promotion of optimizer output into canonical rules.

Evidence from a run that includes an excluded module must name that variant.

## Implementation status

Executable game `0.14.18` implements `0.8.0-rc.19-test` under engine coverage
`nineteen-hex-simplified-v1`. Each Production replaces the prior Power
allocation; its cubes remain on the map as the authoritative powered/offline
snapshot for later rules. The executable uses the complete radius-two board,
six shared Programs, Research Protection, a forty-card Training deck, solo
Mega-Clusters, one direct 1-for-1 trade, automatic Audit penalties, binary
Advanced Networks, and deterministic evidence-backed Dossier resolution.
Browser-native deterministic play, server-backed LLM play, replay, policies,
and Monte Carlo share that contract. The published root now presents the
playable game as its primary action. The public deployment now contains only
the public playtest allowlist; complete documentation, evidence, simulation,
and deferred content remain in a separately built internal review artifact.

Candidate `0.8.0-rc.19-test` changes no physical mechanic from rc.18.
Executable `0.14.18` keeps the thematic Bible as the sole editorial authority
and the Era situation ledger as its machine-enforced traceability projection.
Deployment profiles now own their exact web and Lab source allowlists; the
validator derives their import and runtime-data closure before the builder may
publish. The public browser receives required Programs and match copy while
deferred Tactics and secret objectives remain excluded.

Candidate `0.8.0-rc.18-test` changes no physical mechanic from rc.17.
Executable `0.14.17` adds the machine-enforced Era situation ledger, binds all
62 current Era-bearing surfaces exactly once, rejects deferred material in the
public baseline, and makes Firebase publish only the public playtest profile.
The complete internal review profile is explicitly non-deployable because it
has no access control.

Candidate `0.8.0-rc.17-test` changes no physical mechanic from rc.16.
Executable `0.14.16` binds the published root to the canonical browser icon so
the live navigation and game journey complete without a failed asset request.

Candidate `0.8.0-rc.16-test` changed no physical mechanic from rc.15.
Executable `0.14.15` published the complete browser-module closure required by
the selected-rules game. Physical Chrome must populate both setup selectors
and begin a game without a failed module request before deployment.

Candidate `0.8.0-rc.15-test` changed no physical mechanic from rc.14.
Executable `0.14.14` corrected the generated decision prose for the Public
Capability Covenant and Reorganization, removed unreachable joint-funding
choices from the solo Mega-Cluster contract, and made the deferred cooling
corridor remain explicitly wartime. Every current player-facing source is
regenerated from the content graph. No balance or physical-play evidence
transfers merely because the prose and published navigation changed.

Candidate `0.8.0-rc.14-test` changes no physical mechanic from rc.13.
Executable `0.14.13` preserves every stable component ID, rule, Era count, and
Headline count while extending the canonical four-Era history. Progress now
includes useful cybernetics and subscription biology. Capacity includes
locally compliant robot congestion, biological utilities, and a jointly owned
water bridge between states that remain at war. Authority adds licensed-organ
testimony and machine-readable pollinator corridors. Continuity makes those
systems a metropolitan nervous system and a living watershed seeking standing.
The lore contract binds each idea to an existing component or Era panel. No
balance or physical-play evidence transfers merely because the prose changed.

Candidate `0.8.0-rc.13-test` changes no physical mechanic from rc.12.
Executable `0.14.12` preserves every stable component ID, rule, Era count, and
Headline count while adding the Billion-Instance Bloom to Authority and making
its sensor license the Continuity precedent for self-replicating maintenance.
The lore completeness contract now checks Era panels, actions, resources,
locations, board motions, training faces, power contracts, factions,
Headlines, Mandates, Programs, reference aids, world copy, endings, and every
deferred card surface. No balance or physical-play evidence transfers merely
because the prose changed.

Historical candidate `0.8.0-rc.12-test` changed no physical mechanic from
rc.11. Executable `0.14.11` made the Thematic Content Bible the sole lore
authority. The former scratchpad's placement decisions, research boundaries,
and retained backlog moved into the Bible; the parallel source and orphaned
rendered page were removed. All twelve deferred Tactics, twelve reserve
Specialists, and eighteen Secret Objectives expressed the same four-Era causal
history without entering baseline play. The playable browser and documentation
index adopted the current box premise.

Historical candidate `0.8.0-rc.11-test` changed no physical mechanic from
rc.10. Executable `0.14.10` preserved every stable Headline and Program ID, rules
effect, profile boundary, Era count, card count, and unlock timing while
completing the selected four-Era narrative across the world primer, endings,
Programs, Mandates, faction surfaces, companions, and published galleries. The
retained internal Program ID `open_weights` now presents as Public Capability
Covenant in Authority; strategic Open Weights remains a Progress Headline.
Firebase publication copies only graph-declared runtime artifacts, preventing
ignored legacy projections from remaining publicly addressable. Existing
balance evidence remains evidence for the unchanged mechanics; it does not
validate the new prose, tone, or commercial presentation.

Mechanics projection contract v2 also removes Headline newswire, quotation,
labels, and other presentation-only fields from the mechanics fingerprint. The
historical v1 fingerprint included those fields, so its digest cannot be
compared directly with v2. Reprojecting the `0.14.8` and `0.14.9` rulesets
through v2 produces the same mechanics digest. Ruleset, playtest-kit, content,
and engine identities still change and remain separately attributable.

Historical candidate `0.8.0-rc.10-test` and executable `0.14.9` preserved every
stable Headline ID and mechanic while replacing the four Era panels and all
twenty-four Headline presentations. That release established the selected arc
but left the Era III Program name and several published narrative surfaces
inconsistent with it.

Historical candidate `0.8.0-rc.9-test` and executable `0.14.8` aligned the
release declaration and version-independent contract tests without changing a
setup value, Core Action, score, component, or Headline mechanic.

Historical candidate `0.8.0-rc.8-test` and executable `0.14.7` carried exact
profile-artifact paths and byte hashes into
the unified balance matrix, retained the complete executed ecology, and rejected
source/profile identity mismatches before a holdout started. No setup value,
Core Action, score, or component changed.

Historical candidate `0.8.0-rc.7-test` and executable `0.14.6` let strategy
evolution inject exact frozen opponent
profile artifacts. It validates profile identity, rejects duplicate and unknown
overrides, executes the complete substituted profiles, and records their source
paths, byte hashes, snapshots, and strategy fingerprints. This closes the gap
between a training ecology's opponent IDs and the exact policy versions used by
its intended holdout. No setup value, Core Action, score, or component changes.

Historical candidate `0.8.0-rc.6-test` and executable `0.14.5` made strategy
evolution distribute each focal-seat match budget across every circular
opponent window. It can calibrate three-, four-,
and five-player fields together against their separate neutral shares, ranks
the largest target miss before mean miss and fitness, and records every roster
window in the report. The historical fixed-window mode remains available only
to reconstruct diagnostics. This engine correction changes no starting
resource, Core Action, scoring rule, or physical component.

Historical candidate `0.8.0-rc.5-test` and executable `0.14.4` made every
simulation placement measure follow the authoritative institutional winner,
including an AGI declaration that replaces the provisional Mandate result.
Mandate remains a separately reported score.
This corrects matchup, rank, supplier-finish, and paired-rule evidence without
changing any playable number or action.

Historical candidate `0.8.0-rc.4-test` and executable `0.14.3` added
profile-scoped Action and Mandate-source telemetry. Their reports retain that
identity; reports using raw Mandate as final placement require the disposition
recorded in their tracked receipt.

Historical `0.13.7` / `0.7.0-rc.13-test` evidence retains its exact old
identity. It does not qualify this redesigned map, component set, action
eligibility, Audit, or endgame.

Synchronization is implementation proof, not balance proof. Structured
balance numbers remain hypotheses until a tracked study receipt replaces their
provenance.

The `0.11.0` / `0.7.0-rc.4-test` correction made eligibility explicit:
select only an Action that resolves from current state or can become legal
through one accepted immediate trade before Act. Simultaneous target loss and
a rejected required trade still create real commitment risk. Purely impossible
choices no longer masquerade as strategy. The same executable evaluates an
immediate trade as one complete exchange, creates post-Act offers from the
post-action resource state, and executes declared persona partner, placement,
and resource preferences. The v10 Codex session motivated this correction but
does not establish balance or human teachability.

The `0.13.0` / `0.7.0-rc.6-test` candidate replaces the rejected fixed gate
with four secret Era Dossier choices and the physical Prediction Bag. It also
removes Declare AGI from the Escalation deck and removes persistent Grid-Ready
state. The executable behavior is synchronized, but Dossier bluffing, final
Audit pressure, perceived fairness, and AGI frequency remain unmeasured.

The `0.12.0` / `0.7.0-rc.5-test` fixed-gate candidate is retained only as
historical evidence. It used a five-percent gate and fourth-power Mandate
selection; those rules are not part of the current game.

The `0.10.2` / `0.7.0-rc.3-test` alignment patch changes no mechanic or
number. It makes the selected integrated physical state authoritative in the
machine-readable player supply, distinguishes Default local Power from
Advanced Networks in runtime copy, and synchronizes component inventories,
profile language, and the explicitly unmeasured complexity forecast. The
renamed supply and round fields are contract corrections, not new pieces or
new procedures.

The `0.10.1` / `0.7.0-rc.2-test` precision patch changes no mechanic or
number. It prints final Generator prices on their only legal Energy districts,
removes the obsolete Energy discounts, describes Faction programs and Power
eligibility without assuming the Advanced Network profile, and uses
Escalation availability on one faction-board track everywhere. It also removes
duplicate loose-component descriptions created by the selected double-sided
and track-based physical forms.

That historical synchronized rules candidate promoted the accepted simplification
package. It removes one Generator and all Influence cubes from every faction
set, reduces printed Faction programs from twenty-four to twelve, and removes
Market Access, Build discounts, Policy Shields, Economic Benchmarks, Experts,
Spotlight, and Public Research Grants. Useful effects resolve immediately as
Runway, Compute, Trust, Scrutiny removal, movement, Team recruitment, or
Mandate. This synchronization proves implementation integrity only; new human
and paired simulation evidence must establish balance, negotiation quality,
and teachability.

The `0.9.1` / `0.6.0-rc.2-test` advancement also changes no physical rule. It
corrects the executable selection contract so every unused Core Action and
every unlocked, unspent Escalation remains legally selectable even when it has
no current resolution. Resolution metadata lets deterministic policies avoid
known dead choices without deleting them. A blocked selection exhausts, and a
blocked Escalation spends its availability, exactly as the physical commitment rule
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

`0.5.0-rc.20-test` selected the historical clarification that ring rotation was district
movement rather than Facility relocation for the then-current Grid-Ready rule, the
two-source Power inventory, and the evidence-selected rule that Everybody Gets
a GPU scores one Mandate per four rivals. It promotes four controlled
conversion changes from the winning-path tolerance confirmation: Demis scores
less public Mandate at Capability nine and twelve except for five-player
Capability twelve; Elon scores one Mandate only when Industrial Velocity
actually reduces a completed Facility’s cost; Jensen’s New Architecture
self-Compute follows accepted licenses with no automatic base; and Customers
four and five score one Mandate each while retaining full income. Every other
numerical rule is frozen pending human evidence.
That Grid-Ready rule was removed in `0.7.0-rc.6-test`. Realignment is retained
only in Advanced Play pending comparative human
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
- Does the nineteen-tile map create useful spatial choice without eliminating
  scarcity or creating compulsory routes?
- Does Default Game preserve enough adaptation without Realignment, and does
  bundled Advanced Play justify its additional interruption?
- Are non-declaration strategies competitive?
- Does emergency generation dominate after its actual Audit cost is attributed?
- Does Loopfold AI lead after each Production?
- Does Mirevanta Works or Research-campus protection flatten Research risk?
- Do all three Grid Generator slots fill before Era IV?
- Is Influence selected for genuine political choices rather than efficient
  Trust scoring?
- Are Reorganization and Public Capability Covenant credible alternatives to their competing
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

## Blind-play closure decisions

The current rules candidate closes the following previously implicit contracts:

- The Card and Board Reference prints every Mandate minimum, every Faction ability’s
  printed unlock Era and timing, and every Headline’s Default/Advanced profile
  requirement. The Era IV card introduces only abilities printed as Era IV; the
  Faction board remains authoritative for earlier abilities.
- Production Power cubes remain on powered Facilities and satisfied
  Mega-Cluster demand as the latest Production snapshot until the next
  Allocate step. Built Facilities without cubes are offline. One shared
  Governance Board ledger retains only the currently revealed Mandate's
  criterion, Setup Collective Trust, and final resolution; scored Mandate
  cards remain face up as history. The visible snapshot is authoritative for
  the next Mandate, powered-Facility Headlines, the Era IV Dossier, and final
  offline penalties.
- Fusion has one dedicated shared marker and therefore one project. Mega-Cluster
  construction is resolved in Initiative order; each Facility has one
  Mega-Cluster host slot, hosts must be locally Power-eligible at proposal and
  partner acceptance, and later projects recheck hosts and pair supply after
  earlier accepted projects.
- An immediate trade is one bilateral exchange with exactly one positive named
  resource line per side. Gifts, bundles, and future promises are not legal;
  same-type exchanges are legal but do not trigger Dovetalis Deal Flow.
- Frontier is never controlled and never counts toward the hex-category Mandate.
  Orisonix’s printed Safety cap is four. Dovetalis gains one Runway when its
  Strategic Partnership forms. Influence Joint Venture proposals must use the
  acting piece’s destination Facility.
