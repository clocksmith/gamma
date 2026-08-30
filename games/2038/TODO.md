# Mandate 2038 gameplay audit

This ledger records gameplay defects and blind-play ambiguities found by
comparing the authored rules and card data, the physical specification, and the
selected-rules executable. Generated `dist/` artifacts are projections and are
not independent authorities. Each checkbox is one finding; a checked finding
has an authored ruling, aligned executable behavior where applicable, and a
focused regression or blind-play contract in executable `0.14.16` and rules
candidate `0.8.0-rc.17-test`.

Closure evidence is concentrated in `tests/gameplay-audit.test.mjs` for the
decision-level mechanics, `tests/engine.test.mjs` for Training and map helpers,
`tests/complexity-reduction.test.mjs` for Power endpoints,
`tests/content-graph.test.mjs` and `tests/contracts.test.mjs` for printed and
physical authorities, and `tests/simulation.test.mjs` for complete-match
regressions. `npm run check` verifies generated projections and both immutable
release identities.

## Rules-breaking executable mismatches

- [x] **G2038-001 — Training Run banking is chosen before the run instead of after each safe reveal.**
  - Evidence: `content/copy/core-rules.md:710-717` lets the player bank or continue after any non-duplicate card. `lab/environment/core-economy-match.js:422-433` offers only a preselected `stopAt` value from 2 through 7, and `web/src/engine.js:255-321` banks automatically when `seen.size` reaches it.
  - Problem: a player cannot bank after the first card, cannot react to the actual sequence of reveals, and may not receive a decision after a special card because several specials do not change `seen.size`.
  - Closure: represent bank/continue as a decision after each eligible reveal, retain that decision sequence in replay evidence, and test banking after the first ordinary card and after each special card.

- [x] **G2038-002 — Curated Corpus does not become a duplicate when every ordinary domain is already present.**
  - Evidence: `content/copy/core-rules.md:730-732` says Curated Corpus is a duplicate when no ordinary domain remains. `web/src/engine.js:290-295` simply does nothing when `firstMissingDomain()` returns no domain.
  - Problem: the executable continues a run that the physical rule crashes or protects.
  - Closure: route the no-domain case through the normal protectable-duplicate decision and add a seven-domain Curated Corpus regression.

- [x] **G2038-003 — The second Synthetic Loop does not resolve as its own unprotectable duplicate.**
  - Evidence: `content/copy/core-rules.md:737-741` makes the second Synthetic Loop the duplicate. `web/src/engine.js:306-311` no-ops on the second Loop and only marks the next duplicate as unprotected.
  - Problem: a second Loop can be survived, while an unrelated later domain receives the crash behavior intended for that Loop.
  - Closure: crash immediately on the second Loop without offering protection, consume no later card, and test consecutive and separated Loop copies.

- [x] **G2038-004 — Licensed Dataset is forced whenever Runway is available.**
  - Evidence: `content/copy/core-rules.md:735-736` gives the player a choice between paying one Runway to continue and declining to bank. `web/src/engine.js:299-305` always pays when Runway is positive.
  - Problem: the executable removes a risk-management choice and spends a resource without consent.
  - Closure: add an explicit pay/continue versus decline/bank decision and cover both branches at zero and positive Runway.

- [x] **G2038-005 — Duplicate protection is automatic and its competing sources cannot be chosen.**
  - Evidence: duplicate protection is optional in `content/copy/core-rules.md:722-726`; Scientific Method is also an optional paid reaction in `content/copy/factions.json:70-74`. `web/src/engine.js:274-285` automatically spends Safety, while `lab/environment/selected-rules-match.js:2572-2603` makes Scientific Method available only when Safety is zero and the acting piece is not at Research.
  - Problem: players cannot accept a crash, preserve Safety, choose the Research visit effect, or choose Scientific Method when more than one protection is legal.
  - Closure: expose one reaction decision listing every legal protection plus crash, then test resource use and once-per-Era state for each choice.

- [x] **G2038-006 — Unique-domain effects use Capability gained instead of the domains actually banked.**
  - Evidence: the Training result already returns `distinctDomains` in `web/src/engine.js:324-338`. The Demonstration Holds Mandate, Scaling-Law Breakthrough, and The Matter Compiler Enters Public Maintenance count domains in `content/copy/mandates.json:48-51`, `content/copy/factions.json:77-81`, and `content/copy/headlines.json`. `lab/environment/selected-rules-match.js:2642-2658,2677-2680` uses the Capability delta instead.
  - Problem: Benchmark Leak contributes two false domains, Scientific Method penalties can erase real domains, and Synthetic Loop is included in `seen.size` despite being a special Training type rather than an ordinary domain.
  - Closure: return and consume an explicit banked ordinary-domain set, define whether any special counts for each effect, and test every special card against all three consumers.

- [x] **G2038-007 — Maintained Reality Is Certified can never award Mandate in the executable.**
  - Evidence: `content/copy/mandates.json:60-63` qualifies positive Scrutiny additions and rewards the smallest qualifying amount; `content/data/mandates.json:92-98` sets minimum qualification to 1. `lab/environment/selected-rules-match.js:4028-4030` returns the negative amount, then `lab/environment/selected-rules-match.js:4036-4038` rejects every negative value against that minimum.
  - Problem: every otherwise valid player becomes unqualified.
  - Closure: separate qualification from ranking direction, then test a unique low scorer, a tie, zero additions, and mixed positive totals.

- [x] **G2038-008 — The Fund Mandate records the printed gain rather than Runway actually gained after the cap.**
  - Evidence: caps apply immediately after gains in `content/copy/core-rules.md:231-239`; the Mandate asks for Runway gained through Fund in `content/copy/mandates.json:72-75`. `lab/environment/selected-rules-match.js:2635-2640` adds the requested `actual` amount to `fundRunway` even if `addResource()` clipped the gain.
  - Problem: a player near the Runway cap can score credit for resources returned to supply.
  - Closure: measure the post-cap Runway delta for each Fund resolution and test Capital and Headline modifiers at 11 and 12 Runway.

- [x] **G2038-009 — Immediate Facility effects are counted as Compute produced during Production.**
  - Evidence: `content/copy/core-rules.md:871-873` says immediate Facility production is not a second Production. `lab/environment/selected-rules-match.js:3458-3527` increments `roundMetrics.computeProduced` inside `produceFacility()` regardless of its `stage`; that helper is also called by immediate effects at `lab/environment/selected-rules-match.js:1392-1397,4670-4675`.
  - Problem: The Passive Citizen Dividend Activates and Orbital Compute can inflate the Compute Becomes a Public Condition Mandate.
  - Closure: count Compute only when the helper runs in the Production or Partner boxes, and test identical Facility output in immediate and Production contexts.

- [x] **G2038-010 — Joint Venture Compute is omitted from Compute produced during Production.**
  - Evidence: Joint Ventures produce in the Partner box under `content/copy/core-rules.md:608-611`, and the Mandate counts Compute produced during Production in `content/copy/mandates.json:54-57`. `lab/environment/selected-rules-match.js:3862-3889` grants the exchanged resource without incrementing `roundMetrics.computeProduced` when that resource is Compute.
  - Problem: the physical score sheet and executable disagree for active compute-side Joint Ventures.
  - Closure: count post-cap or gross production according to one explicit ruling, apply it symmetrically to both partners, and add Runway/Compute contract regressions.

- [x] **G2038-011 — Frontier Research grants an unprinted extra Capability.**
  - Evidence: Frontier's complete visit effect is optional Runway plus Scrutiny in `content/copy/map-reference.md:79-83`. `lab/environment/selected-rules-match.js:2659-2661` grants one additional Capability after any successful Research ending at Frontier.
  - Problem: the executable contains a hidden location bonus with no card or rule authority.
  - Closure: remove the bonus or author it explicitly, then add a Frontier-versus-ordinary-location Research parity test.

- [x] **G2038-012 — Organize Recruit omits its additional movement.**
  - Evidence: `content/copy/core-rules.md:776-777` recruits and then moves one CEO or Team up to two additional adjacent hexes. `lab/environment/selected-rules-match.js:2476-2504` recruits and returns immediately.
  - Problem: a legal positioning benefit never occurs in executable play.
  - Closure: add a post-recruit optional movement decision for any owned CEO or Team, including zero, one, and two-step paths.

- [x] **G2038-013 — Organize Redistribute cannot divide five steps among pieces.**
  - Evidence: `content/copy/core-rules.md:778` allows a combined total of five adjacent steps across CEOs and Teams. `lab/environment/selected-rules-match.js:1757-1778,2506-2513` selects one extra piece and teleports it to a tile at axial distance at most five.
  - Problem: the executable cannot split movement, cannot express multi-piece paths, and can cross intermediate geometry without recording steps.
  - Closure: model an ordered sequence of up to five legal adjacent moves, permit stopping early, and test split movement and path-dependent board states.

- [x] **G2038-014 — Reorganization makes arbitrary movement and return choices for the player.**
  - Evidence: `content/copy/core-rules.md:382-389` lets the player move each Team up to one hex and optionally choose one Team to return. `lab/environment/selected-rules-match.js:3258-3273` moves every Team to the first enumerated board option and returns the first Team found.
  - Problem: control and adjacency can change without player choice; the selected decision's movement fields do not govern resolution.
  - Closure: collect a destination or stay choice for each Team and an explicit optional return identity, then verify the exact chosen pieces move.

- [x] **G2038-015 — The Company Brain Survives Bankruptcy replaces Organize instead of modifying it.**
  - Evidence: the Headline says “During Organize” in `content/copy/headlines.json:14-19`. `lab/environment/selected-rules-match.js:1885-1903,2529-2537` creates a standalone `employee_free` resolution, returns the first N Teams, and performs none of Organize's three modes.
  - Problem: using the Headline forfeits the printed Organize action and prevents choosing which positioned Teams return.
  - Closure: make Team returns an optional modifier around a normal Organize resolution and require explicit Team identities.

- [x] **G2038-016 — Cost reductions are applied after base legality has already removed actions.**
  - Evidence: replacement, surcharge, and discount order is defined in `content/copy/core-rules.md:241-242`. Base generation requires one Compute for Research and two Runway for a Facility in `lab/environment/core-economy-match.js:422-445`; selected-rule adjustments occur later in `lab/environment/selected-rules-match.js:2058-2144`.
  - Problem: legal zero-Compute Cloud Research and one-Runway discounted Facility or Clean Infrastructure builds can be absent before their waiver or discount is evaluated.
  - Closure: compute the effective cost before affordability filtering for every action lane and test Cloud, Chip, Industrial Velocity, and Orbital Power Receives a Beam Corridor at the exact reduced cost.

- [x] **G2038-017 — The deepfake Regulate surcharge can resolve without being paid.**
  - Evidence: `content/copy/headlines.json:149-155` adds one Compute to Deploy. `lab/environment/selected-rules-match.js:2759-2761` subtracts it only after resolution and clamps the balance at zero, rather than including it in legal cost calculation.
  - Problem: a player with only the base Deploy cost can complete an action that should be unaffordable.
  - Closure: include the surcharge in effective cost before selection and test insufficient, exact, waived-base, and remote Social Graph Deploy cases.

- [x] **G2038-018 — The deepfake vote effect expires after its reveal cycle instead of lasting to Era end.**
  - Evidence: `content/copy/headlines.json:149-155` says the selected regime lasts from the vote until Era end. `lab/environment/selected-rules-match.js:1400-1408` stores the result in `regime.cycle`, and later Deploy handling reads only that cycle at `lab/environment/selected-rules-match.js:2759-2763`.
  - Problem: later cycles in the same Era ignore the chosen policy.
  - Closure: store the vote in Era-scoped state and test Deploy in the reveal cycle and every later cycle.

- [x] **G2038-019 — Do Nothing rewards Customers gained before the deepfake vote.**
  - Evidence: `content/copy/headlines.json:152` limits the bonus to Customers gained after the vote. `lab/environment/selected-rules-match.js:3892-3899` compares final Customers with the Era-start snapshot.
  - Problem: Customers gained in earlier cycles receive unearned additional Production income.
  - Closure: snapshot Customer count when the vote resolves and calculate only later gains, including gains from non-Deploy effects.

- [x] **G2038-020 — The Court Adopts Supported Meaning hard-codes two rivals instead of half rounded up.**
  - Evidence: `content/copy/headlines.json:106-111` requires at least half of the controller's rivals, rounded up. `lab/environment/selected-rules-match.js:4713-4721` checks `rivals.length >= 2` for every player count.
  - Problem: the threshold is wrong in supported three-player and six-player games.
  - Closure: derive `Math.ceil((playerCount - 1) / 2)` and test every supported player count.

- [x] **G2038-021 — Emergency Power is committed before the actions that determine Production demand.**
  - Evidence: `content/copy/headlines.json:98-103` assigns emergency Power during Production. `lab/environment/selected-rules-match.js:1501-1512` asks for 0–2 immediately after the Headline resolves, before action selection, then consumes the stored number at `lab/environment/selected-rules-match.js:3577-3583`.
  - Problem: players must choose without knowing final Facilities, projects, trades, or demand, and the physical and executable timing differ.
  - Closure: move the choice into the Allocate box after ordinary capacity and trades are known.

- [x] **G2038-022 — The Social Graph disappears when the controlled remote tile is reachable normally.**
  - Evidence: `content/copy/factions.json:44-48` permits any controlled Consumer or Media destination without moving there. `lab/environment/selected-rules-match.js:1999-2031` excludes every tile already present among normal movement resolutions.
  - Problem: if any acting piece can reach that tile, the player cannot choose to leave the piece in place and use the remote ability.
  - Closure: generate remote variants independently of normal destination variants and preserve the acting piece's original position.

- [x] **G2038-023 — Allocation Window does not create usable unsold temporary Compute.**
  - Evidence: `content/copy/factions.json:161-165` creates temporary Compute before offers and says all remaining tokens disappear at cycle end. `lab/environment/selected-rules-match.js:1023-1049` permits `allocation_hold`, while `lab/environment/selected-rules-match.js:1076-1099` creates value only when a sale is accepted.
  - Problem: the Foundry may skip the required offer, and a rejected or unsold token never exists for the Foundry to spend before expiry.
  - Closure: instantiate both temporary tokens on the Foundry, require one complete offer per token, transfer accepted tokens, and expire remaining temporary units wherever held.

- [x] **G2038-024 — Export Controls does not block Allocation Window Compute sales.**
  - Evidence: `content/copy/headlines.json:89-95` prohibits Compute trades for the cycle. `lab/environment/selected-rules-match.js:1313-1318` sets `computeTradeBlocked`, but Allocation Window executes through `lab/environment/selected-rules-match.js:996-1103` without checking it.
  - Problem: the faction can sell Compute during a cycle in which no Compute trade is legal.
  - Closure: route Allocation Window through the same trade-legality contract as immediate trades and add blocked/open cycle tests.

- [x] **G2038-025 — An isolated Generator becomes an Advanced Network anchor.**
  - Evidence: `content/copy/advanced-play.md:19-34` starts the graph at the first Facility or a Link and propagates through adjacent owned sites. `web/src/engine.js:707-740` first adds every Facility adjacent to any Generator, then propagates from all of those Facilities.
  - Problem: a disconnected Generator-Facility island joins the Network without a path to the starting grid or a Link, enabling pooled Power and the Network bonus illegally.
  - Closure: traverse from the starting-grid Facility and linked Facilities across Facility/Generator adjacency; do not seed from every Generator.

- [x] **G2038-026 — Mega-Cluster Power is assigned after, and outside, the player's allocation choice.**
  - Evidence: `content/copy/core-rules.md:600-606` tells players to allocate Power to Facilities and Mega-Clusters. `lab/environment/selected-rules-match.js:3721-3769` offers only Facility subsets; `lab/environment/selected-rules-match.js:3796-3831` then powers projects automatically in creation order from leftovers.
  - Problem: players cannot prioritize competing solo or joint projects, and partners have no physical procedure for coordinating scarce extra demand.
  - Closure: include project demand in each participant's allocation decision, define joint-project consent and contention order, and test two projects competing for the same final Power.

- [x] **G2038-027 — A joint Mega-Cluster can be initiated only from the lead host.**
  - Evidence: `content/copy/core-rules.md:358,365-372` allows the acting piece to end on either host. Solo choices enumerate both hosts in `lab/environment/selected-rules-match.js:2164-2183`; joint choices require and record only the lead's left host in `lab/environment/selected-rules-match.js:2192-2215`.
  - Problem: otherwise legal joint projects are missing when the acting piece can reach only the partner host.
  - Closure: enumerate both hosts as legal destinations while preserving ownership and payment roles.

- [x] **G2038-028 — Joint Mega-Cluster Scrutiny ownership is unspecified, but the executable assigns it to the lead.**
  - Evidence: construction adds two Scrutiny in `content/copy/core-rules.md:350-354`; joint costs and outputs are split in `content/copy/core-rules.md:365-372` without assigning that Scrutiny. `lab/environment/selected-rules-match.js:3244-3257` gives both cubes to the lead.
  - Problem: physical players cannot resolve the cost from the written rule, while the executable has made an undeclared balance decision.
  - Closure: state whether the lead takes both, each participant takes one, or another split applies; print it on the card and test that exact split.

- [x] **G2038-029 — A rejected Advanced Power request may target the same rival again.**
  - Evidence: `content/copy/advanced-play.md:62-67` requires the second request to a different rival Network even after rejection. `lab/environment/selected-rules-match.js:3587-3612,3669-3687` excludes a supplier only after an accepted sale.
  - Problem: the second request can repeat the first rejected supplier.
  - Closure: track requested supplier identities per buyer independently from the once-per-Production supplier-sale limit.

- [x] **G2038-030 — Executable Production resolves its resource producers in the wrong order.**
  - Evidence: `content/copy/core-rules.md:608-611` orders powered Facilities, Customer income, Mega-Clusters, then numbered Joint Ventures. `lab/environment/selected-rules-match.js:3796-3899` resolves Mega-Clusters, Facilities, Joint Ventures, and Customers.
  - Problem: resource caps and effects that inspect current resources can produce different outcomes between physical and executable play.
  - Closure: implement the printed box and sub-order exactly, with a cap-sensitive regression demonstrating each boundary.

- [x] **G2038-031 — Scrutiny overflow penalties are chosen automatically.**
  - Evidence: `content/copy/core-rules.md:633-637` lets the player pay Runway or lose Trust when both are available. `lab/environment/core-economy-match.js:183-195` always spends Runway first.
  - Problem: the executable removes a consequential player choice every time the ten-cube supply overflows.
  - Closure: make overflow resolution an attributable decision per excess cube and test both choices plus one-option and no-option states.

- [x] **G2038-032 — Audit penalties are chosen automatically.**
  - Evidence: `content/copy/core-rules.md:655-662` gives an available payment choice in Eras I–III and the defined Era IV fallback. `lab/environment/selected-rules-match.js:3967-4012` always spends Runway whenever the configured amount is available.
  - Problem: players cannot preserve Runway by accepting Trust or Mandate loss.
  - Closure: make each colored and Systemic Risk hit a player decision when multiple legal consequences exist, retaining Initiative/order semantics.

- [x] **G2038-033 — Agent Swarm offers known-unresolvable Core Actions and converts them into forced no-ops.**
  - Evidence: `content/copy/core-rules.md:423-427` says to resolve two different unused Core Actions and pay all costs. `lab/environment/selected-rules-match.js:3303-3318` includes unused actions with zero current resolutions; `lab/environment/selected-rules-match.js:3321-3337` then manufactures a forced no-op.
  - Problem: the rules do not say a player may spend half of Agent Swarm on an action already known to have no resolution.
  - Closure: either filter zero-resolution choices or explicitly authorize the no-op in the rulebook, then test actions made illegal by the first Swarm resolution.

- [x] **G2038-034 — The Shovels does not define whether Agent Swarm's two Core Actions aggregate into one spend.**
  - Evidence: `content/copy/factions.json:153-158` triggers on at least two Compute spent “in one action.” Agent Swarm resolves two Core Actions in `content/copy/core-rules.md:423-427`, but `lab/environment/selected-rules-match.js:4600-4605` measures Compute before and after the entire selected Escalation.
  - Problem: two separate one-Compute Core Actions trigger The Shovels in the executable, while the physical wording can reasonably be read as two non-qualifying spends.
  - Closure: define the accounting unit for compound actions and test 1+1, 2+0, and one discounted subaction.

## Blind-play and physical specification gaps

- [x] **G2038-035 — “Adjacent rival Power connection” has no complete Default Game endpoint rule.**
  - Evidence: Default Game explicitly has local Power rather than a Network in `content/copy/core-rules.md:257-265`, while the trade rule uses “adjacent rival Power connection” in `content/copy/core-rules.md:593-599`. The executable defines adjacency as any adjacent pair of currently eligible buyer and supplier Facilities in `lab/environment/selected-rules-match.js:3596-3611`.
  - Problem: physical players cannot tell whether adjacency is measured from Generator to Facility, powered Facility to powered Facility, or any locally eligible Facility pair.
  - Closure: name both endpoints and whether they must be powered, merely eligible, or connected to exportable Generator capacity; mirror that definition in the UI.

- [x] **G2038-036 — Escalation card faces omit their unlock Era and timing metadata.**
  - Evidence: `content/data/escalations.json:21-52` records `unlockedRound` and `timing` for every card. `content/copy/card-reference.md:206-244` projects only name, rules text, and flavor while telling players to select an unlocked card.
  - Problem: a separated card or Card Reference entry does not tell a blind player when it is legal.
  - Closure: print the Era and timing on every Escalation face and include them in the generated Card Reference.

- [x] **G2038-037 — The Era III reference card omits immediate Power purchases.**
  - Evidence: the authoritative unlock rule introduces Joint Ventures and immediate Power purchases in `content/copy/core-rules.md:391-395`. The Era III card in `content/copy/reference-cards.json:22-28` says only “agreements” plus the two named Escalations.
  - Problem: a table following the Era rail can reach Production without learning that Power trading is now legal.
  - Closure: name Joint Ventures and immediate Power purchases explicitly on the Era III card.

- [x] **G2038-038 — Training card faces have no projected gameplay text.**
  - Evidence: `content/copy/component-reference.md:3-5` says printed Training cards own their exact text, and `content/copy/card-reference.md:3-6` claims to collect every card effect. Its Training section at `content/copy/card-reference.md:608-623` includes only names and flavor, while all special behavior exists only in `content/copy/core-rules.md:728-743`.
  - Problem: the physical card contract and Card Reference cannot independently resolve Curated Corpus, Licensed Dataset, Benchmark Leak, Synthetic Loop, or Human Evaluation.
  - Closure: add concise rules text to every Training card data object and project it onto card faces and the reference.

- [x] **G2038-039 — Power Source card faces omit their mechanical contracts.**
  - Evidence: `content/copy/component-reference.md:3-5` gives printed Power cards exact-text authority. `content/copy/card-reference.md:625-645` shows only tagline and public claim, omitting construction site, cost, capacity, Trust, recurring Scrutiny, uniqueness, and Fusion output defined in `content/copy/core-rules.md:817-844`.
  - Problem: the three reference cards cannot perform their stated reference job during construction and Production.
  - Closure: project every mechanical field and timing onto the card faces, with one authoritative cost source.

- [x] **G2038-040 — The Dossier orientation instruction names the wrong card.**
  - Evidence: `content/copy/component-reference.md:84-86` says to place the current Era card face down, while setup gives each player Era-labelled Dossier cards in `content/copy/core-rules.md:44-48` and filing uses the matching Dossier in `content/copy/core-rules.md:625-629`.
  - Problem: literal setup would remove the shared Era card and cannot preserve each player's secret choice.
  - Closure: replace “current Era card” with “current Era's Dossier card” and blind-test the orientation instruction.

- [x] **G2038-041 — Starting-grid identity conflicts between “first constructed Facility” and “Facility 1.”**
  - Evidence: `content/copy/core-rules.md:49-53` and `content/copy/component-reference.md:34-41` assign the grid to the first Facility constructed. `physical/component-spec.md:136-143` permanently assigns it to Facility 1, but no rule requires Facility 1 to be constructed first.
  - Problem: choosing another numbered piece first produces two incompatible physical states.
  - Closure: require numbered construction order, make Facility 1 the mandatory first piece, or use a transferable starting-grid marker; state the selected rule in setup and component specs.

- [x] **G2038-042 — Prediction Bag token source is contradictory.**
  - Evidence: `content/copy/core-rules.md:463-467,493-498` and `physical/component-spec.md:38-46` use faction-coloured Scrutiny cubes as prediction tokens. `physical/component-inventory.md:54-58` says generic track cubes become Prediction Bag tokens.
  - Problem: the inventory does not identify which components enter the bag, and generic track markers may not satisfy the bag's tactile and faction-identity requirements.
  - Closure: select one component source and make the rules, inventory, material specification, and quantities agree.

- [x] **G2038-043 — The physical kit has no defined place to retain World Ending inputs.**
  - Evidence: setup requires recording Setup Collective Trust in `content/copy/core-rules.md:57-59`; final resolution requires final Collective Trust and unresolved Systemic Risk in `content/copy/core-rules.md:487-492,900-920`. `physical/score-sheet.md:1-27` has neither field, and the Governance Board zones at `physical/component-spec.md:64-75` provide no writable ending record.
  - Problem: the table must rely on memory or an improvised private note despite `physical/component-spec.md:109-111,158-161` requiring visible reconstructible state.
  - Closure: add public Setup Trust, final Trust, unresolved Risk, AGI result, and ending fields to a specified board or score-sheet surface.

- [x] **G2038-044 — The final sentence contradicts the Prediction Bag winner replacement.**
  - Evidence: `content/copy/core-rules.md:487-507,885-894` makes Mandate standings provisional and lets a matching eligible claimant become the sole final winner. `content/copy/core-rules.md:941-948` then states without qualification that highest Mandate wins.
  - Problem: a blind reader can ignore the game's final winner-replacement mechanism.
  - Closure: label the Mandate rule as the provisional-winner rule and state that its tie breakers apply before the Prediction Bag.

- [x] **G2038-045 — “Emergency Power” is confusable with Emergency Infrastructure.**
  - Evidence: `content/copy/core-rules.md:593-599` says installed Generator capacity may be sold but “emergency Power” may not. Emergency Infrastructure is itself an installed Generator in `content/copy/core-rules.md:763-767,832-840`; Headline-granted supplemental Power is defined separately in `content/copy/headlines.json:98-103`.
  - Problem: the sentence can be read to forbid selling the Emergency Infrastructure Generator that the preceding clause permits.
  - Closure: name the unsellable source as “Headline-granted supplemental Power” and explicitly confirm whether Emergency Infrastructure capacity is exportable.

- [x] **G2038-046 — Canonical data contains stale Generator costs that conflict with the rules.**
  - Evidence: location-owned construction costs are one and two Runway in `content/data/game-config.json:39-55` and `content/copy/core-rules.md:763-767`. The same power sources carry `runwayCost` values of two and three in `content/data/game-config.json:457-475`.
  - Problem: consumers that read `powerSources[].runwayCost` can display or enforce a different game from consumers that read the location rule.
  - Closure: remove the stale field or make it a validated projection of the single authoritative location cost.

- [x] **G2038-047 — The supported physical inventory still lacks exact generic stock quantities.**
  - Evidence: `physical/component-inventory.md:101-115` leaves Runway, Compute, Safety, temporary Power, generic track markers, player-reference copy count, and board production form unresolved.
  - Problem: the documented box cannot be manufactured, packed, or blind-unboxed without improvising components and risking shortages at legal caps.
  - Closure: derive worst-case public supply requirements for two through six players, select exact quantities and embodiments, and record the final bill of materials before an RFQ or release candidate is called production-complete.

## Release integrity

- [x] **G2038-048 — The current physical rules candidate is stale while declaring itself synchronized.**
  - Evidence: `versions/current-release.json:15-31` includes `physical/component-spec.md` and `physical/component-inventory.md` in `0.7.0-rc.7-test` and labels implementation synchronized. `versions/0.7.0-rc.7-test/manifest.json:34-40` records the old files as 3,688 and 6,710 bytes with hashes `4c316d…` and `c46eca…`; the current files are 4,973 and 10,917 bytes with hashes `77b115…` and `7bb4e6…`. `npm run check` consequently fails at `tasks/create-game-release.mjs:181-190`.
  - Problem: the named candidate does not identify the physical rules now in the repository, so its synchronization and controlled-play identity cannot be reproduced.
  - Closure: preserve the immutable candidate, issue a new candidate version over the current physical sources, update `versions/current-release.json`, and require `node tasks/create-game-release.mjs --verify` to pass before calling it synchronized.

## Deferred optional Tactic module

These findings do not block Default Game or Advanced Play because
`content/data/game-config.json:569` disables Tactics and
`experimental/tactics-rules.md:3-8` excludes them from baseline play and balance
evidence. They do block any future claim that the preserved optional module is
executable.

- [x] **G2038-049 — The optional Tactic module has no executable setup, draw, or play-loop entrypoint.**
  - Evidence: `experimental/tactics-rules.md:13-29` defines a deck, setup deal, Era draw, hand limit, and one-play-per-cycle timing. `lab/environment/selected-rules-match.js:243-275` initializes every hand empty; `lab/environment/selected-rules-match.js:1434-1499` defines `tacticStage()`, but the complete cycle at `lab/environment/selected-rules-match.js:4829-4835` never calls it and no code fills a hand.
  - Problem: the optional module cannot be played through the executable even if a configuration later enables it.
  - Closure: add an explicit module flag, deterministic deck/discard state, setup and Era draws, hand-limit decisions, and a documented play window before promoting Tactics out of `experimental/`.

- [x] **G2038-050 — Cloud Partnership chooses its beneficiary by seat order.**
  - Evidence: `experimental/copy/tactics.json:6-11` says another player gains one Runway without naming a forced recipient. `lab/environment/selected-rules-match.js:1454-1462` always pays the next seat modulo player count.
  - Problem: the executable invents a target and removes the card player's negotiation choice.
  - Closure: require an explicit eligible rival target when the card is played.

- [x] **G2038-051 — Talent Raid recruits at the CEO's current tile instead of the acting piece's destination.**
  - Evidence: `experimental/copy/tactics.json:38-43` places the Team at the acting piece's destination. `lab/environment/selected-rules-match.js:1463-1477` has no acting resolution context and places it at the CEO's current tile.
  - Problem: the card can resolve at the wrong location and cannot accompany a Team acting piece.
  - Closure: move the play window into the player's action resolution and bind the recruited Team to that action's acting piece and destination.

- [x] **G2038-052 — Board Reshuffle chooses which Action to ready automatically.**
  - Evidence: `experimental/copy/tactics.json:46-51` lets the player ready Organize or Influence. `lab/environment/selected-rules-match.js:1478-1480` readies the first matching used Action in array order.
  - Problem: when both are exhausted, the player receives no choice.
  - Closure: offer exactly the exhausted eligible cards as target decisions and consume the Tactic only after selection.

- [x] **G2038-053 — Weights Leak chooses the rival Facility automatically.**
  - Evidence: `experimental/copy/tactics.json:54-59` says to resolve one powered rival Facility. `lab/environment/selected-rules-match.js:1488-1494` selects the first rival with a powered Facility and that rival's first powered Facility.
  - Problem: different Facility productions have different resources and choices, so enumeration order changes card value.
  - Closure: list every Facility powered in the latest Production snapshot and require an explicit target.

- [x] **G2038-054 — Custom Silicon chooses the first Facility automatically.**
  - Evidence: `experimental/copy/tactics.json:70-75` applies permanently to one Facility. `lab/environment/selected-rules-match.js:1481-1482` marks `player.facilities[0]` without a target decision.
  - Problem: Facility identity matters for Power, movement, contracts, and later loss, so the target cannot be inferred safely.
  - Closure: require a Facility identity and retain the attachment in physical and replay state.

- [x] **G2038-055 — Open Letter is not public before votes are committed.**
  - Evidence: `experimental/copy/tactics.json:22-27` and `experimental/tactics-rules.md:25-29` require the option and added vote to be public before anyone commits a vote. `lab/environment/selected-rules-match.js:1167-1195` bundles Open Letter use into each player's simultaneous vote decision and reveals it only while totals are calculated.
  - Problem: other voters cannot respond to the public intervention, changing the strategic procedure.
  - Closure: add a separate precommit Open Letter window, publish its option and extra vote, then collect the ordinary secret votes.
