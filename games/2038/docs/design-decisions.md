# Mandate 2038 Design Decisions

**Rules reference:** `0.10.0-rc.3-test`
**Status:** current rationale and implementation-boundary ledger

This document explains why the selected game has its present shape. It does
not repeat card text or resolve play: `rules.md` is the
rulebook source for the physical game; component records own exact printed effects.

The former complexity-proposal document was folded into this ledger after its
five selected proposals were implemented. Earlier 19-tile, every-Era
map-motion, transmission, Tactic, secret-objective, and endgame-scoring
assumptions are historical only.

## Readable Era overviews

The user wants the original lore with a light narrative touch. `world.md`
therefore presents four Era overviews as a past-tense retrospective from 2038.
Concrete examples and causal transitions give the overview a game-setting
introduction, while unfamiliar terms are explained in ordinary language. All original technologies, institutional consequences, and six
fictional institutions remain explicit. A recurring family, dialogue, and plot
are not part of this presentation. Endings describe independent outcomes in the same past tense.

The earlier duplication cleanup remains: one source for extended setting prose,
one introduction and motto per institution, compact Era panels, and Headline
events with quotes and effects. Writing notes follow the fiction. The guided
match retains its route; obsolete standalone lesson files remain removed.

The site home and documentation overview each present a title and a single list
of links. Section groups, card descriptions, promotional introductions, and
visible build metadata have been removed from those indexes. Existing pages
remain available; release identity remains in build receipts.

Executable `0.15.6` and candidate `0.9.0-rc.7-test` record the revised prose and
indexes. Engine identity `0.17.4` records the site-builder change. Game mechanics,
timing, costs, scoring, and ending conditions are unchanged. These are editorial
and presentation changes, not a balance promotion.

## One ruleset — 2026-09-05

The user selected removal of the alternate play layer. The game now uses a
fixed map, local Power, sixteen Headlines, and three player-aid panels.
Mode selection, extra infrastructure components, market requests, map ballots,
and the supplemental Headline procedures are removed from authored sources,
runtime, and generated references. Retired selectors fail before play begins.

This removes the former extension while preserving the ordinary game's costs,
scoring, faction authority, and four-Era progression. Shared scenario notes
remain with surviving components; unique themes are carried by their existing
Era framing. Historical releases retain their original rules and evidence.
This user-selected change makes no claim about measured balance or human
teachability.

## Authoring consolidation — 2026-09-05

Game procedures, map instructions, component states, and supported inventory
prose now share one authored rulebook. Named excerpts generate the compact Core
Rules and detailed references. Component records continue to own exact effects;
reference layouts arrange those fields without rewriting them. The editing and
build map is `content/README.md`.

This changes authoring ownership and generated presentation, with no changes to
selected mechanics, simulation code, or browser implementation. Runtime content
changes only in release metadata. New local release identities preserve the
previous immutable bundles; this is not a balance promotion or publication.

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

An ordinary action may combine its printed rule, one destination bonus, each applicable
faction modifier, and applicable global state. Persistent Headlines use
physical reminders. Every exception has a timing window. A current Headline
overrides an older global effect only when both alter the same field.

Tactics remain a deferred module because the baseline already contains enough
variation to test the central engine.

### Eras teach the game

- **Progress:** Agent assignment, Core Actions, Research, Facilities, Customers, and
  Scrutiny.
- **Capacity:** Generators, Mega-Clusters, and early Programs.
- **Authority:** persistent agreements and competing public realities.
- **Continuity:** Agent Swarm, Fusion, AGI, and the civilizational ending.

Later systems remain visible from setup, but the Current Era panel is the sole unlock
authority.

### Presentation cannot create a new phase

ReAct names Reason, Act, and Observe within the existing turn. It creates no
extra event, reward, reaction window, or phase. Production reads current
connections, produces, and resolves partnerships. Era IV recognition precedes
the final Audit and ordinary Mandate scoring.

### Mandate stays public

Customers, Capability thresholds, Trust thresholds, Era Mandates, Fusion, and
faction awards score when they occur. Facilities and control create
position and production rather than receiving automatic endgame points. Final
calculation applies the offline penalty and ordinary score tie breakers.
Public AGI recognition has already awarded its fixed Mandate before the Audit.

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

Power delivery is local: a Generator can power its owner’s Facilities on its
own hex or an adjacent hex. The starting grid powers its assigned Facility.
Generators and Mega-Clusters unlock in Era II. The randomized jurisdiction
remains fixed for all four Eras.

Fusion deliberately occupies one of the Grid tile’s three Generator slots.
Filling those slots can deny Fusion; the first controlled test must measure
whether that creates meaningful spatial competition or an accidental lockout.

## Selected interaction contract

One immediate resource trade may occur before a player’s resolution: offer
exactly one Runway for one Compute, or the reverse, to a named counterparty.
The counterparty accepts or rejects. Influence is required to propose or
terminate a persistent Joint Venture and to change Trust or Scrutiny.

Influence is an action, not a component supply. The acting Agent must be assigned
at Media, Government, or Capital to change Trust or Scrutiny. Political control
counts each Agent and Facility as one presence; ties remain
uncontrolled. A Joint Venture must be proposed or terminated by an acting piece
at one of the player’s Facilities. Joint Ventures use numbered neutral host
pairs. Their operation depends on printed range and current Generator connections.

Promises about later turns are not binding. The game supports negotiation
without requiring a general contract-enforcement system.

## Rule-change register

The generated [rule-change register](../dist/docs/rule-change-register.md)
records decisions and implementation state. The game has one ruleset; the
register does not offer selectable combinations of procedures.

Future complexity reductions are governed by the
[`complexity-reduction-protocol.md`](complexity-reduction-protocol.md). The
August 2026 package established the previous baseline: one location-defined Generator,
presence-only politics, two programs per Faction, removal of seven stored-token
families, and one set of local Power and interaction procedures.
The register records them as accepted current decisions.

## Selected risk and ending contract

Audit draws scale by player count. Scrutiny beyond a player’s ten physical
cubes immediately becomes a Runway-or-Trust penalty. Era IV Audit converts
risk into Runway or Mandate loss so late exposure remains consequential.

AGI is an optional public achievement after Era IV Production. Qualification
uses Capability, connected Facilities, and Trust; payment consumes Compute and
awards fixed Mandate plus Scrutiny before the Audit. Each institution may
declare once. The final Mandate winner uses the ordinary tie breakers; recognized
AGI selects the separate World Ending axis and never replaces that winner.
The ending is Open only when collective Trust improves beyond setup by the
player count and unresolved Systemic Risk remains below the player count.
Winning and building the preferable future remain separate achievements.

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

Executable game `0.17.0` implements `0.10.0-rc.3-test` under coverage
`react-agent-assignments-v1`: direct persistent Agent assignments, speculative
selection, unprotected Research with printed faction exceptions, current local
Power connections, and optional AGI recognition scored within Mandate. The
nineteen-hex board, six shared Programs, forty-card Training deck, solo
Mega-Clusters, one direct 1-for-1 trade, and automatic Audit remain.

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
machine-readable player supply and synchronizes component inventories,
Power language, and the explicitly unmeasured complexity forecast. The
renamed supply and round fields are contract corrections, not new pieces or
new procedures.

The `0.10.1` / `0.7.0-rc.2-test` precision patch changes no mechanic or
number. It prints final Generator prices on their only legal Energy districts,
removes the obsolete Energy discounts, describes Faction programs and Power
local Power eligibility, and uses
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

The `0.9.0` / `0.6.0-rc.1-test` advancement changed the interaction and map
procedures. Those historical rules and reports do not qualify the current
ruleset; immutable releases retain the exact earlier contracts.

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
That Grid-Ready rule was removed in `0.7.0-rc.6-test`. Later revisions also
removed the alternate map and market procedures.

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
- Does the fixed jurisdiction preserve satisfying spatial adaptation across all four Eras?
- Are non-declaration strategies competitive?
- Does emergency generation dominate after its actual Audit cost is attributed?
- Does Loopfold AI lead after each Production?
- Do paid Scientific Method banking, Orisonix crash retention, or the Research-campus banking bonus flatten Research risk?
- How often do players forgo an immediate destination bonus to preserve district presence?
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
  printed unlock Era and timing, and every Headline’s procedure. The Era IV card introduces only abilities printed as Era IV; the
  Faction board remains authoritative for earlier abilities.
- Facility 1 is always powered. Other Facilities use current own-Generator
  adjacency for production, contracts, Headlines, qualification, and penalties.
  The shared ledger retains permanent Program use, the current Mandate criterion,
  Setup Collective Trust, and final public recognition. Scored Mandate cards
  remain face up as history.

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

<!-- decision-register:start -->
This generated register records selected design decisions and their
implementation state. The canonical procedures are in the Core Rules; exact
component effects remain with their component records.
<!-- decision-register:end -->


## Full simplification candidate

Decision ID: `user-selected-full-simplification`. The user requested the complete
redesign after reviewing executable 0.15.6 and rules 0.9.0-rc.7-test. This is a
user-selected structural candidate, not a promotion motivated by simulated wins.

- Replace CEO and Team piece types with four identical Agents, two initially
  deployed. Assign directly to any district, retaining presence. CEOs remain
  faction characters. Organize recruits one Agent or relocates a Facility.
- Check only card availability and unlocks at simultaneous selection. Assign,
  pay, and choose targets during resolution. A blocked selection assigns and
  exhausts. Preserve six Actions and three cycles in each of four Eras.
- Remove universal Research Protection. Retain paid Scientific Method banking;
  Orisonix retains one revealed Capability on a crash; Research districts add
  one Capability on a bank. Special Training cards remain.
- Replace numeric Power and snapshot authority with current local connections.
  Facility 1 stays powered; an own Generator connects its own and adjacent
  districts. Mega-Clusters need two adjacent connected hosts, with no extra demand.
- Recognize AGI after final Production at 9 Capability, 2 connected Facilities,
  4 Trust, and a payment of 3 Compute. Award 4 Mandate and add 2 Scrutiny before
  Audit. Every qualifying player may declare; ordinary final Mandate decides
  the winner. Recognition persists through Audit and determines the AGI axis
  of the separate World Ending.
- Loopfold's Social Graph now gains one Runway on its first controlled Consumer
  or Media Deployment in an Era. Orbital Compute relocates before assignment
  and immediately produces only if connected. Reorganization reassigns Agents;
  any recall leaves at least one deployed. Fusion is a second local connection
  site with its existing cost and printed Mandate, subject to its shared supply.
- Emergency Power Authority adds two Compute and one extra Scrutiny during
  Production to institutions whose emergency Generator serves a Facility.
  The AGI Blog Post grants the Capability leader one Trust immediately; it
  never changes the fixed recognition award. These replace retired subsystems.
- Record named Program use in permanent six-box faction rows; returning the
  two Era markers does not erase history. The turn aid applies all applicable
  faction modifiers and excludes Tactics from baseline play.

All replacement values above are unbalanced test hypotheses. Validate rule and
runtime agreement first; compare Research, Power, AGI, and Agent assignment
separately against archived versions, then the combined candidate. At four
players, human sessions must record rules questions, stopping decisions,
Production handling, endgame explanation, and deliberately blocked selections.
Three- and five-player completion and faction integrity need separate evidence.
Simulation cannot establish teachability, enjoyment, or physical handling time.
Historical release bundles and previous evidence remain immutable.

## Additive institutional vignettes

On 2026-09-06 the user supplied seven additional situations spanning Progress, Capacity, Authority, and Continuity. Their full prose joins the existing World companion, with connective passages and shorter echoes on seven existing Headlines, four Mandates, and two Programs. Existing scenario definitions and Era causal threads gain the corresponding concepts; all earlier lore, card titles, quotations, effects, identities, and quantities remain. Biological hosts extend the fiction of Agents without changing their assignment rules. Orbital credits, forecasts, and bodily operating rights are setting material, not new resources or procedures.

Executable `0.16.1` and rules candidate `0.10.0-rc.2-test` record this content addition. The engine remains `0.18.0`; the mechanics are unchanged from executable `0.16.0`. Preservation checks compare the prior immutable bundle with the authored and generated content. This is a content release, with no new claim about balance or human playtest evidence.

## Review closure and Talent reassignment

The review of commit `37745ed3` identified an incomplete transition. Commit `43557bd7` already synchronized Agent setup, speculative selection, Research, local connections, scored AGI, and the seven Era stories. This follow-up corrects surviving current-status and selection prose in the evidence and simulator documentation, while retaining historical receipts under their original identities. AGI labels and the automated AGI Candidate's instructions now describe scored recognition, immediate Compute trades, and connected Joint Ventures; they no longer teach Publication, winner replacement, or delivered Power.

The user-selected Talent change replaces executable `0.16.1`'s interim one-Runway production with one Agent reassignment. The selected-rules engine offers the same Agent/district combinations as ordinary assignment, including staying. Presence updates immediately; the reward grants no Action, destination bonus, exhaustion, or additional resource. Only connected Talent Facilities produce, in normal Production order; effects that invoke printed Facility production also invoke this reward. Joint Ventures continue to grant their printed contract resource rather than full host production.

Executable `0.17.0`, engine `0.19.0`, and candidate `0.10.0-rc.3-test` record this mechanical delta. The browser, simulator, generated tile/reference copy, and tests share that contract. The core-economy diagnostic remains a partial engine and explicitly excludes Talent reassignment. Physical components and supply counts need no change. No price, Research value, AGI threshold, or other balance parameter changes.

The World companion preserves every supplied vignette and the existing concepts, connects employment and intelligence access to later ownership, explains live-state migration limits alongside matter compilers, and keeps forecasts contested. The next human test records forgone destination benefits and preserved control. No human session or balance result is claimed by these implementation checks.

Validation also reproduced a pre-existing report-archive collision: parallel LLM fixture matches with the same seed, job label, and millisecond timestamp shared a temporary and final filename. Each archive now receives a unique suffix and always cleans its own temporary file. A concurrency regression checks that every report survives independently. This changes evidence storage, not simulated outcomes; the archive implementation is included in the release engine identity.

## Three cuts candidate

The user selected three further simplifications after reviewing executable 0.17.0: immediate Headlines, removal of Programs with a Facility-plus-project Build, and one permanent mechanical idea per faction. Implementation and isolated checks follow that order. Existing lore, current map, Agent presence, ordinary Research, shared risk, and scored AGI remain. No AGI qualification or general scoring value is lowered to compensate without evidence. This is a design candidate, not a measured complexity or human-balance result.

Headlines finish every choice before Core Action selection. Voluntary resource/risk offers, current control rewards, recruitment or retirement, and immediate connected Facility production preserve different incentives. They leave no price modifier, later trigger, permission, or reminder token. Narrative and event history remain.

Build places a Facility first, then one project from the same Agent assignment;
requirements are checked after placement. The combined plan must be affordable.
The two project references replace the six Program cards. No Program marker,
permanent use ledger, temporary Compute token, or extra Core Action remains.
Former Program and secondary ability fiction is retained in the existing Era
companion and faction references as lore with no game effect.

Provisional faction values: Dovetalis gains 1 Runway after its own optional trade;
Loopfold gains 1 Runway after Deploy; Mirevanta pays 1 Runway to bank a duplicate;
Kestralyn's Facilities cost 1 less Runway; Orisonix retains up to 1 provisional
Capability on a crash; Corthaven gains 1 Runway per rival with a Facility during
Production, capped at 2. Corthaven's board-state condition replaces a spending
ledger and avoids uncapped player-count scaling. Starting assets are unchanged;
all factions use common Capability scoring. These are test values, not a balance claim.

The [dated implementation study](../evidence/studies/2026-09-06-three-cuts.md)
records isolated Headline and construction diagnostics, the combined candidate,
source/hash identities, and limits. The final small four-player sample built no
advanced projects; the three- and five-player samples each built one Mega-Cluster.
AGI was recognized in one of 24 final four-player games. No thresholds were tuned
from these results. Human testing must establish construction attractiveness and
whether preserving Agent presence warrants forgoing immediate destination bonuses.

The remaining old Power-demand Mandate was a correctness bug: its removed metric
always read zero. It now counts connected Facilities plus operating Mega-Clusters
on the current board, preserving its minimum of two and two-Mandate award.
