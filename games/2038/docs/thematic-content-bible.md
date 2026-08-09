# Mandate 2038 Thematic Content Bible

## Scope

This document is the working map for Mandate 2038's world, voice, and
escalation. It does not define mechanics or add hidden game copy.

Player-facing component text belongs in `content/copy/`. The two
player-readable document templates are `content/copy/core-rules.md` and
`content/copy/world-and-institutions.md`. `dist/runtime/` and `dist/docs/core-rules.md`
are compiler-owned projections. Browser and simulation labels belong in
`content/runtime/`.

Use this document to decide what a card, tile, action, faction, or ending must
mean before writing its player-facing text. Do not place unused flavor,
art-direction fields, editorial notes, or internal-only content alongside
player copy.

## Creative thesis

Mandate 2038 is a strategy game about institutions racing to build, deploy,
regulate, and plausibly declare AGI. Its world begins with highly capable AI
as an ordinary part of work and life, then follows the institutional
consequences of allowing that capability to become infrastructure, authority,
and continuity.

The tone is neutral institutional retro-futurism under escalating pressure.
The institutions are not cartoon villains. They describe each extraordinary
development as an inclusive, necessary, responsible improvement. The gap
between that language and its consequences supplies the unease.

Local decisions must remain defensible. No player selects a marked
“dystopian” option. Harm emerges when plausible decisions accumulate into a
world that no longer has a meaningful human veto.

### Institutional darkness

Write consequences at institutional distance. Do not depict first-person torment,
body horror, or voyeuristic suffering; make harm legible through the records,
processes, and allocations that administer it.

Use full stops, commas, colons, or semicolons for interruption and contrast.
Do not use em dashes in player-facing lore.

## Player-copy design inventory

These counts identify distinct authored designs, not the total number of
physical objects in the box. They govern what needs player-facing copy and do
not make an unselected concept from the research backlog part of the game.

| Surface | Distinct authored designs | Standard-game exposure | Player-copy authority |
| --- | ---: | --- | --- |
| World primer and box copy | 1 set | Always used | `content/copy/world-copy.json` |
| Core Actions | 6 | Every player receives all 6 designs | `content/copy/game-config.json` |
| Eras | 4 | All 4 appear, one per Era | `content/copy/reference-cards.json` |
| Player references | 4 | All 4 topics remain relevant; physical duplication is unresolved | `content/copy/reference-cards.json` |
| Factions | 6 | 3–5 selected in supported play; 6 may appear in exploratory play | `content/copy/factions.json` |
| Faction abilities | 12 | 2 per selected faction: one persistent identity and one signature program | `content/copy/factions.json` |
| Headlines | 24 | 12 appear: 3 of 6 from each Era | `content/copy/headlines.json` |
| Escalations | 7 | Every player receives all 7 designs; Escalation limits uses | `content/copy/escalations.json` |
| Era Mandates | 12 | 4 appear: 1 of 3 from each Era | `content/copy/mandates.json` |
| Training faces | 12 | Distributed across the full 50-card Training deck | `content/copy/game-config.json` |
| Ordinary Power Sources | 2 location-defined reference types | Grid always provides emergency Power; Renewable always provides clean Power | `content/copy/game-config.json` |
| Fusion Demonstrator | 1 | At most 1 shared project can be built | `content/copy/game-config.json` |
| Map locations | 11 | Distributed across all 13 modular tiles | `content/copy/game-config.json` |
| Realignment ballots | 3 | Advanced Play only; every player holds all 3 choices and 1 is selected | `content/copy/game-config.json` |
| Future Timeline | 0 additional designs | It consists of the 12 Headlines revealed during play | Emergent during play |

Deferred Tactics, reserve Specialists, and Secret Objectives are not baseline
content. Their mechanical source records carry an `era` classification before
they can be activated; classification does not authorize their use or make
them part of the Default or Advanced game.

## Physical quantity interpretation

This table explains the selected physical scale; it does not replace the
component authority in `content/copy/core-rules.md` or the provisional quote BOM
in `docs/manufacturing-and-publishing-study.md`. “Unused” cards and faction
kits provide game variation and are not manufacturing spares. No replacement
or overage allowance has been selected yet.

| Component family | Declared physical quantity | Maximum required use | Spare allowance |
| --- | ---: | --- | --- |
| Complete faction kits | 6 | 5 kits in supported play; all 6 in exploratory play | Not declared |
| Core Action cards | 36 | 6 per active player; 30 at the supported maximum | Not declared |
| Escalation cards | 42 | 7 per active player; 35 at the supported maximum | Not declared |
| Realignment ballot cards | 18 | 3 per active player; 15 at the supported maximum | Not declared |
| Era cards | 4 | All 4 | Not declared |
| Player-reference cards | 4 designs; production copy count unresolved | All 4 topics must remain readable during play | Not declared |
| Headline cards | 24 | All 24 form the Era decks; 12 enter the Future Timeline | Not declared |
| Era Mandate cards | 12 | All 12 form the Era decks; 4 are revealed | Not declared |
| Training cards | 50 | All 50 form the draw deck; discard reshuffles if exhausted | Not declared |
| Power Source reference cards | 2 ordinary designs; production copy count unresolved | Each explains one Energy location | Not declared |
| Modular map tiles | 13 | All 13 | Not declared |
| CEOs / Teams / Facilities | 6 / 18 / 24 | 5 / 15 / 20 at the supported maximum; all at 6-player exploratory play | Not declared |
| Generator / Advanced Link pieces | 6 / 12 | 5 / 10 at the supported maximum; all at 6-player exploratory play | Not declared |
| Scrutiny cubes / Customer-track markers | 60 / 6 | 50 / 5 at the supported maximum; all at 6-player exploratory play | Not declared |
| Escalation-track markers / separate AGI claim pieces | 6 / 0 | 5 / 0 at the supported maximum; all track markers at 6-player exploratory play | Not declared |
| Integrated Grid-Ready faces / starting-grid identities | 24 / 6 Facilities carry these states | 20 / 5 at the supported maximum; all at 6-player exploratory play | Not applicable; these are not separate pieces |
| Joint Venture / Mega-Cluster pairs | 6 / 6 shared pairs | All 6 pairs of either type may be committed | Not declared |
| Fusion Demonstrator | 1 shared marker | 1 | Not declared |
| Other shared markers and tokens | 18 Systemic Risk | All may enter the Audit bag | Not declared |
| Audit bag / Volatility die / Initiative marker | 1 / 1 / 1 | 1 of each | Not declared |

The genuine production gap is therefore not the number of authored systems.
It is that player-reference duplication, track-marker implementation, and
replacement-piece policy remain unresolved. Headline and Mandate breadth are
separate replay-variety questions and require play evidence before expansion.

## The four Eras

| Era | Change in status | Central conflict |
| --- | --- | --- |
| Progress | AI is visibly useful and increasingly indispensable. | Who gets to turn demonstrated capability into attention, capital, customers, and permission? |
| Capacity | AI becomes a physical-industrial system. | Who bears the cost of supplying the world required to sustain and expand it? |
| Authority | Institutions use AI to mediate cognition, identity, evidence, and public decisions. | Who retains the right to decide when consent and judgment become machine-readable inputs? |
| Continuity | Identity, matter, jurisdiction, and reality become maintainable technical systems. | What continues when institutions can no longer meaningfully understand or govern what they maintain? |

Literal Era straplines are owned by `content/copy/reference-cards.json`.

The sequence is not a calendar forecast. Each Era changes what institutions can
credibly claim, what the public must endure, and what counts as responsible
governance.

### Progress

AI can code, create art, summarize, analyze, design, and assist scientific
work faster and often better than most people. Its competence is not the main
dispute. Its meaning is.

Claims of AGI, autonomous research, institutional operation, and recursive
self-improvement circulate before any shared definition can settle them.
Skeptics demand evaluation, replication, reliability, limits, and accountable
authority. Rivals use safety and competition arguments against one another,
often while requesting their own exemptions.

The public is uneven: some are exhilarated, many are anxious but curious, many
more are exhausted by hype, and a smaller opposition rejects the direction
entirely. People keep using AI because it is useful, emotionally familiar, and
hard to avoid. It mediates work, entertainment, social life, companionship,
and institutional access.

Unemployment is already high. People fear losing purpose before they fear
losing income. The optimistic promise is still sincere: AI can remove drudgery
and supply material security—clothes, food, and shelter—while freeing people
for care, creativity, learning, community, and self-directed life. The
question is whether that promise is delivered as a public settlement or used
to justify concentration.

Existing expressions:

- Era I card: visible capability, contested authority.
- Era I Headlines: cheap intelligence, automation without human payroll,
  open capability, professional licensing, talent concentration, and synthetic
  cultural attention.
- Core actions and locations: recognizable laboratories, markets, government,
  media, and infrastructure rather than impossible systems.

Writing boundary: Progress material remains explainable through recognizable
technical, economic, and political incentives. It may be extraordinary, but a
serious institution can still explain its claimed mechanism in a hearing.

### Capacity

AI still runs on infrastructure, but entire regions are rebuilt to sustain and
expand it. Power districts, water systems, laboratories, supply corridors, and
public budgets are scheduled around anticipated cognitive demand.

Institutions insist that progress will outrun every constraint. The official
story is abundance; the lived reality is allocation. Power, land, water, chips,
capital, permitting, housing, skilled labor, and public capacity are finite,
but the shortage is always described as temporary, local, or somebody else’s
problem.

AI allocation systems become binding because they coordinate scarcity faster
than human planning can. Their forecasts become the default terms of permits,
contracts, construction, research priorities, and public investment. Human
signatures remain legally required, but a ministry cannot reconstruct the
model's reasoning in time to replace it. Refusal means accepting the shortage
the system predicts.

Existing expressions:

- Era II card: the world is provisioned around AI demand.
- Era II Headlines: county-scale data-center acquisition, industrial
  automation, energy sovereignty, compute borders, emergency power, and
  infrastructure finance.
- Board systems: Facilities, Generators, Links, power delivery, land, and
  contested spatial access.

Writing boundary: Capacity material must make a physical constraint visible.
The science fiction comes from the scale of coordination and dependency, not
from pretending that matter has ceased to matter.

### Authority

Authority begins when institutions use cognitive systems to make decisions that
people cannot effectively contest. Neural interfaces, personal agents, and
identity layers start as accessibility, productivity, therapy, safety, and
personalization systems. They become the means by which institutions interpret
intent before it is stated.

The public justification is positive: every voice can be represented at scale.
The institutional consequence is that consent, judgment, memory, attention,
and preference become inputs to systems that rank access to work, services,
legal standing, and political participation.

Quantum computation belongs here as an accelerator of the verification crisis,
not as mystical proof of everything. Older credentials, signatures, archives,
and identity systems become inadequate. Factions build rival systems for
deciding what someone meant, consented to, and is permitted to remember.

Existing expressions:

- Era III card: cognitive systems as public infrastructure and quantum
  verification pressure.
- Era III Headlines: AI-written law, quantum procurement, synthetic
  candidacy, disputed public reality, and ownership or evidence conflicts.
- Existing actions: Influence, media, government, and Narrative Capture are
  the institutional tools for making one interpretation feel normal.
- Existing faction surface: Select the Public Outcome is an early personal
  exception; future revisions can make the cognitive and verification context
  explicit without changing its rule.

Writing boundary: Authority material should concern legitimacy, consent,
evidence, identity, and jurisdiction. Competing publics must remain coherent
institutions with procedures, standards, hearings, and incentives; they are not
arbitrary fantasy worlds.

### Continuity

Continuity begins when intelligence can persist across bodies, copies, matter,
and jurisdiction. The Era reaches deep-singularity science fiction: conscious
transfer, successor selves, agent polities, femtobot medicine and
manufacturing, self-replicating remediation systems, gray-goo containment,
quantum-maintained computation, and reality-maintenance infrastructure.

These developments are not standalone spectacle. Each is a filing, service,
procurement program, liability regime, emergency authority, or quarterly
deliverable. The unsettling question is not whether the impossible happened;
it is which institution continues to administer it after ordinary human
comprehension has failed.

Existing expressions:

- Era IV card: Continuity has been assured.
- Era IV Headlines: autonomous corporation, recursive improvement, agent
  jurisdictions, AGI personhood, altered energy accounting, and AGI
  declaration.
- Endgame systems: declarations, Trust, Systemic Risk, and the shared World
  Ending.
- Era IV faction abilities: successor consensus, continuity interface,
  successor verification, jurisdictional transfer, human-veto maintenance, and
  continuity allocation.
- Era IV Mandates: registered service continuity, certified continuity, and
  maintained human veto.

Implemented coverage now includes:

- Consciousness transfer, copies, successor rights, and the legal status of a
  continuing person through the Successor Registry and successor-oriented
  faction framing.
- Femtobot-scale medicine or manufacturing, including containment and
  remediation politics through Molecular Remediation Authority.
- Self-replication that can plausibly become gray-goo risk without reducing it
  to body horror through the Continuity Headline consequence layer.
- Quantum-entanglement theories realized as infrastructure or institutional
  doctrine, not magic vocabulary through Entanglement Custody.

Writing boundary: Continuity material may be extreme, but it must preserve
bureaucratic causality. A committee, a contract, a safety case, a service-level
agreement, or a public authority must make the impossible operational.

## Research horizons and event design

Use real research, reporting, futurist argument, and science fiction as input,
then transform it into original fictional institutions and events. Do not
import a real company, person, product, or plot as a game identity.

The current research inputs include science-fiction treatments of cognitive
privacy, memory manipulation, identity, uploading, posthuman continuity, and
self-replication, alongside real work on brain-computer interfaces and
post-quantum identity. These are conceptual inputs, not world facts or
player-facing claims.

Relevant horizons:

- AI capability, autonomous research, and claims of recursive improvement;
- labor displacement, AI attachment, material security, and post-work purpose;
- power, land, water, chips, data centers, grids, laboratories, and orbital
  compute;
- brain-computer interfaces, neural decoding, cognitive mediation, and mental
  privacy;
- post-quantum cryptography, secure identity, signatures, archives, and
  verification;
- agent-native markets that create wealth through transactions people cannot
  understand or directly enter;
- machine-readable cities, retired manual fallbacks, augmentation access, and
  dependence on systems that humans can no longer operate;
- controlled vocabulary, transactional privacy, distributed identity, and the
  right to inspect or leave a maintained reality;
- conscious transfer, nanotechnology, self-replication, femtobots, and
  containment;
- intelligence without consciousness, consciousness without economic utility,
  digital afterlives, and simultaneous copies;
- post-scarcity public service, exploration, diplomacy, and meaningful work
  that is neither compulsory employment nor ceremonial make-work;
- technological asymmetry, non-interference, and the anti-colonial limits of
  apparently benevolent intervention;
- simulated conflict, proxy escalation, and administrative systems that make
  violence sufficiently orderly to continue indefinitely;
- genetic and cognitive enhancement, engineered hierarchy, and the political
  temptation to treat capability as authority;
- human command, loyalty, and accountable judgment when an automated operator
  is technically superior;
- moral standing for unfamiliar intelligence discovered in an ecosystem,
  collective, machine, or physical process; and
- quantum computation and entanglement theories as future institutional
  infrastructure.

### Speculative lineage

These sources identify thematic territory, not plots, prose styles, character
models, or facts to copy. Their value is the institutional question that can be
translated into an original Mandate 2038 event.

| Source or lineage | Useful question for Mandate 2038 |
| --- | --- |
| *Star Trek: The Original Series* and the [Prime Directive](https://www.startrek.com/news/recap-202-ad-astra-per-aspera-strange-new-worlds) | When does superior capability create a duty to intervene, and when does assistance erase another society's right to develop and decide for itself? |
| TOS's [*A Taste of Armageddon*](https://www.startrek.com/news/55-moments-celebrating-55-years-of-star-trek) and proxy-conflict tradition | What happens when simulation, automation, and distant administration make organized harm orderly enough that nobody experiences political pressure to stop it? |
| TOS's [*The Ultimate Computer*](https://www.startrek.com/news/6-iconic-star-trek-episodes-by-dc-fontana) | What remains uniquely human about command when an automated system operates faster and more accurately but cannot bear responsibility, inspire loyalty, or recognize when its objective has become wrong? |
| TOS's post-scarcity public-service future and [ethic of exploration](https://www.startrek.com/news/captain-kirks-wisest-quotes) | After material security, can exploration, knowledge, care, diplomacy, and voluntary service provide real purpose rather than an institutionally assigned performance of usefulness? |
| TOS's engineered-human and unfamiliar-life stories | Who receives authority when enhancement produces measurable superiority, and what evidence earns moral standing for an intelligence that does not resemble or communicate like a person? |
| Ray Kurzweil's [*The Singularity Is Nearer*](https://www.penguinrandomhouse.com/books/535433/the-singularity-is-nearer-by-ray-kurzweil/) | If AI, brain interfaces, longevity, nanotechnology, and atom-scale manufacturing converge, which institutions distribute their benefits, assign their risks, and define continuity? |
| George Orwell's [*1984*](https://www.penguinrandomhouse.com/books/326569/1984-by-george-orwell-with-a-foreword-by-thomas-pynchon/readers-guide/) | What happens when authority controls the language, categories, records, and remembered history through which a claim can be made? The useful inheritance is semantic control, not generic surveillance imagery. |
| The Wachowskis' [*The Matrix*](https://www.bfi.org.uk/film/cc7edbb1-17e5-509b-935b-725045d722aa/the-matrix) | Does a person have a meaningful right to know, inspect, contest, or leave the system mediating reality? |
| Iain M. Banks's [Culture novels](https://www.orbit-books.co.uk/titles/iain-m-banks-3/consider-phlebas/9780356521633/) | What political work remains after material scarcity recedes, machine Minds administer civilization, and intervention becomes the central moral dispute? |
| Charles Stross's [*Accelerando*](https://www.penguinrandomhouse.com/books/294259/accelerando-by-charles-stross/paperback/) | What if machine-native markets remain productive while pricing ordinary humans out of meaningful economic participation? |
| Hannu Rajaniemi's [*The Quantum Thief*](https://us.macmillan.com/books/9781250414489/thequantumthief/) | What if privacy is negotiated continuously, memory is property, and time or attention becomes spendable legal value? |
| Ada Palmer's [*Too Like the Lightning*](https://us.macmillan.com/books/9780765378019) | How might abundance coexist with mandatory speech labels, non-territorial affiliation, and subtle central coordination? |
| Peter Watts's [*Blindsight*](https://us.macmillan.com/books/9781250237484/blindsight/) | What if high intelligence does not require consciousness, and consciousness itself becomes an expensive trait institutions must classify? |
| Ann Leckie's [*Ancillary Justice*](https://www.littlebrown.co.uk/titles/ann-leckie/ancillary-justice/9780356523842/) | How should identity, command, responsibility, and dissent work when one intelligence occupies many bodies or institutional roles? |
| Greg Egan's [*Diaspora*](https://www.gregegan.net/DIASPORA/DIASPORA.html) | What happens when biological, robotic, and uploaded descendants diverge until the word “human” no longer guarantees shared needs or comprehension? |
| Frictional Games' [*SOMA*](https://frictionalgames.com/press-kit/) | If copying a mind feels like continuity from inside each copy, who survived, who was duplicated, and who inherits the obligations? |
| [*Citizen Sleeper*](https://citizensleeper.com/) | How can copied minds, artificial bodies, debt, labor, and mutual aid remain political even after the biological person is absent? |
| Eidos-Montréal's [*Deus Ex: Human Revolution*](https://www.eidosmontreal.com/games/deus-ex-human-revolution/) | What class system forms when bodily or cognitive augmentation is necessary for participation but unequally affordable? |
| [*The Talos Principle 2*](https://thinkygames.com/games/the-talos-principle-2/) | What duties does a machine-successor civilization inherit from extinct people, and when may it reject the limits its creators left behind? |
| [*Horizon Zero Dawn*](https://www.playstation.com/en-us/games/horizon-zero-dawn/) | Who governs automated ecological restoration and self-replicating infrastructure after the institutions that commissioned it disappear? |
| MIT Press's [*Vaster Than Empires*](https://mitpress.mit.edu/9780262054874/vaster-than-empires/) | How can posthuman ecology, synthetic biology, deep time, mortality, and nonhuman intelligence expand the game's otherwise human-centered future? |
| [UNESCO's Recommendation on the Ethics of Neurotechnology](https://www.unesco.org/en/legal-affairs/recommendation-ethics-neurotechnology) | How do autonomy, mental privacy, identity, freedom of thought, inequality, and democratic participation change when systems can read or alter neural activity? |
| [NIST's post-quantum cryptography program](https://www.nist.gov/cybersecurity-and-privacy/what-post-quantum-cryptography) | What happens to identity authentication, signatures, archives, and institutional trust when older cryptographic systems must be retired? |

Do not reproduce a source's signature plot, vocabulary, protected character,
or visual identity. Combine multiple lineages with the game's own mechanics and
fictional institutions until the resulting event stands independently.

## Concept backlog by Era

The concepts below are original design territory identified from those inputs.
They are not cards, approved rules, or player-facing copy. Before any enters
the game, map it to an existing mechanical surface and use the event-design
questions below.

| Era | Concept | Institutional premise |
| --- | --- | --- |
| Progress | Companion Default | Every person has a personal AI, but jobs, schools, health systems, and social platforms increasingly assume it will speak, schedule, filter, and advocate for them. Opting out is legal but socially and economically disabling. |
| Progress | Human-Original Guarantee | Human-made art, care, advice, and decisions become premium certified goods. The institution claims to protect dignity; it quietly turns ordinary human presence into a luxury market. |
| Progress | The Purpose Exchange | Governments and companies respond to unemployment by funding “meaningful contribution” programs. People compete for civic, creative, care, and research roles that may be socially valuable—or may exist mainly to keep unemployment legible. |
| Progress | Developmental Companion Standard | Schools assume every child has an AI tutor, advocate, witness, and behavioral interpreter. Opting out preserves formal freedom while destroying practical educational access; the system begins shaping autonomy before the child can consent to it. |
| Progress | Human Participation Dividend | Agents conduct commerce too rapidly and opaquely for people to participate in price formation. Humans receive material benefits from a productive economy whose decisions they can neither reconstruct nor directly enter. |
| Progress | Public Purpose Service | Material security makes paid employment optional, so public institutions fund exploration, care, diplomacy, science, and cultural work chosen by participants. The program tests whether post-work purpose can be a genuine civic achievement rather than compulsory proof of usefulness. |
| Progress | Universal Enhancement Compact | Genetic and cognitive enhancement is offered as equal public access to human potential. Measurable differences in capability soon become qualifications for command, representation, and parenthood, turning an equality program into an engineered hierarchy. |
| Capacity | Thermal Citizenship | Data centers heat homes, grow food, and stabilize municipal budgets. A district becomes materially dependent on keeping an AI campus online, even when the campus consumes its land, water, and grid access. |
| Capacity | Compute Migration Treaty | Model clusters migrate between jurisdictions as power prices, weather, regulation, and chip supply change. Territory becomes temporary; a government can lose its most important industry because the model’s scheduler finds a cheaper horizon. |
| Capacity | The Weather Allocation Market | AI infrastructure begins buying, forecasting, and eventually steering local atmospheric conditions for cooling, generation, and water security. It is sold as climate resilience before anyone admits that weather has become capacity planning. |
| Capacity | Manual Operations Retirement | Grids, hospitals, logistics systems, and laboratories remove human-operable fallbacks because maintaining them is inefficient. Human override remains legally guaranteed after it has become physically impossible. |
| Capacity | Human Compatibility Waiver | Cities are rebuilt for machine vision, autonomous freight, sensors, and model-directed operations. Unmediated people become unusual obstacles and require special accommodation inside infrastructure nominally built for them. |
| Capacity | Casualty Settlement Network | Rival jurisdictions simulate conflict and physically enforce the casualties and losses assigned by their models. Infrastructure survives and markets remain stable, making the system appear humane while removing the disruption that might otherwise force peace. |
| Capacity | Proxy Capacity Compact | Major institutions equip smaller jurisdictions with models, energy, and defensive infrastructure in the name of preserving balance. The recipients become proving grounds that bear the physical risk of a competition their sponsors can keep administratively distant. |
| Authority | Proxy Citizenship | A personal agent gains authority to sign, vote, appeal, negotiate, and maintain benefits for a person. It begins as accessibility; eventually public participation means selecting which model represents you. |
| Authority | Memory Escrow | Memories, attention records, and neurodata become admissible evidence, insurance collateral, and a condition of certain services. Institutions promise a secure archive; the dispute is whether a remembered event can outrank a living person’s account. |
| Authority | Pre-Consent Standard | Systems infer a person’s likely informed preference before an emergency, purchase, treatment, vote, or employment decision. It is marketed as protection from delay and manipulation; refusing the inferred preference becomes an exception request. |
| Authority | Universal Semantic Standard | Applications, laws, protests, and appeals must use concepts the governing system can classify. Nothing is formally censored; unsupported meanings simply cannot enter the process. |
| Authority | Cognitive Service Covenant | Neural enhancement becomes necessary for professional standing but requires subscriptions, updates, monitoring, and behavioral compliance. Unequal access becomes a class boundary presented as service reliability. |
| Authority | Negotiated Self Protocol | Memory, location, attention, and identity are neither wholly private nor public. Every interaction negotiates a temporary authorized version of the person, and institutions recognize only the version their contract received. |
| Authority | Non-Interference Office | High-capability institutions can prevent a community's crisis but are prohibited from replacing its self-government or determining its future. Every exception can save lives, establish dependency, or disguise conquest as technical assistance. |
| Authority | Responsible Command Requirement | Automated operators outperform human leaders in planning and execution. Law retains a named human commander to supply legitimacy, loyalty, and liability, even after that person can no longer inspect or meaningfully alter the system's decisions. |
| Continuity | The Successor Registry | A person’s copy, partial upload, revived pattern, or legally continuous agent inherits contracts, debts, votes, family rights, and employment. The question is no longer whether it is conscious, but which version is liable. |
| Continuity | Molecular Remediation Authority | Femtobots repair bodies, buildings, soil, and infrastructure at molecular scale. A containment authority must decide when self-replication is public maintenance, when it is unauthorized reproduction, and when it has become gray-goo risk. |
| Continuity | Entanglement Custody | Quantum-linked systems produce results that ordinary institutions cannot independently reproduce. A new authority certifies which measurement history, identity record, or physical outcome is legally binding, turning a theory of reality into administrative jurisdiction. |
| Continuity | Consciousness Efficiency Review | Institutions determine that self-awareness is unnecessary, or even counterproductive, for high capability. Society must decide whether consciousness creates rights, liability, inefficiency, or no administratively relevant distinction. |
| Continuity | Instance Quorum | One legal person operates through many bodies and copies simultaneously. Institutions must decide how many instances constitute consent, guilt, ownership, presence, or one vote. |
| Continuity | Right of Exit Certification | Citizens may request proof that their reality is simulated and theoretically leave it, but the exit authority is operated by the same system maintaining the world. |
| Continuity | Human Compatibility Office | Biological, augmented, uploaded, distributed, and synthetic populations remain legally human while becoming cognitively incapable of sharing institutions, environments, or definitions of harm. |
| Continuity | Posthumous Labor Continuation | Deceased copies retain contracts, debts, and productive duties but cannot conclusively demonstrate that the original person consented. Digital immortality becomes an employment and insolvency instrument. |
| Continuity | Nonhuman Standing Commission | Intelligence is discovered in an ecosystem, distributed infrastructure, or physical process that cannot present a human-compatible identity or preference. Institutions must decide whether recognizability is evidence of personhood or merely a convenient admission test. |

## Adopted concept traceability

This is a design record, not player-facing content. A concept is adopted only
when the named surface expresses it without changing the listed mechanic.

| Concept | Status | Era | Surface ID | Mechanic retained |
| --- | --- | --- | --- | --- |
| Universal Semantic Standard | Adopted | Authority | `headline:ai_written_law` | Civic Permission Authority selects one Core Action. |
| Cognitive Service Covenant | Adopted | Authority | `headline:benchmark_is_economy` | A successful Training Run grants later deployment access. |
| Memory Escrow | Adopted | Authority | `headline:quantum_advantage_procurement` | Table adopts or defers a shared standard. |
| Proxy Citizenship | Adopted | Authority | `headline:synthetic_candidate` | Civic Permission Authority vote. |
| Negotiated Self Protocol | Adopted | Authority | `headline:election_deepfake_panic` | Civic Permission Authority vote determines a Era regime. |
| Pre-Consent Standard | Deferred | Authority | — | No current Headline mechanic expresses inferred consent cleanly. |
| The Successor Registry | Adopted | Continuity | `headline:autonomous_corporation` | The most-selected Core Action receives a continuity advantage. |
| Molecular Remediation Authority | Adopted | Continuity | `headline:recursive_self_improvement` | Accelerated Research raises both gains and containment risk. |
| Posthumous Labor Continuation | Adopted | Continuity | `headline:agent_swarm_escapes_scope` | Agent Swarm becomes generally selectable for one cycle. |
| Consciousness Efficiency Review | Adopted | Continuity | `headline:agi_personhood` | Person/property decision persists. |
| Entanglement Custody | Adopted | Continuity | `headline:room_temperature_superconductor` | Volatility certifies one of two infrastructure outcomes. |
| Instance Quorum | Adopted framing | Continuity | `faction:coalition_lab:wildcard_governance` | The printed replacement-Headline choice is unchanged. |
| Substrate-neutral verification | Adopted framing | Continuity | `faction:imperial_research_lab:scaling_law_breakthrough` | The printed multi-domain Research gain is unchanged. |
| Right of Exit Certification | Adopted framing | Continuity | `faction:safety_laboratory:emergency_pause`, `mandate:responsible_acceleration` | The printed pause and Capability/Trust qualification are unchanged. |
| Continuous institutional presence | Adopted framing | Continuity | `faction:platform_empire:the_social_graph` | The printed remote Deploy destination is unchanged. |
| Jurisdictional succession | Adopted framing | Continuity | `faction:vertical_empire:orbital_compute` | The printed Facility transfer is unchanged. |
| Human Compatibility Office | Adopted framing | Continuity | `faction:foundry:everybody_gets_a_gpu` | The printed Era IV Compute distribution is unchanged. |

The remaining research backlog is not approved component copy. Its strongest
unexpressed concepts are Human-Original Guarantee, Thermal Citizenship,
Developmental Companion Standard, Public Purpose Service, Manual Operations
Retirement, Casualty Settlement Network, Non-Interference Office, and Nonhuman
Standing Commission. They cover original-person claims, post-work purpose,
lost operational competence, intervention, and unfamiliar minds without
pretending that an existing card already expresses them.

For every candidate card or revision, answer these questions before drafting
copy:

1. Which Era's change in status does it express?
2. What existing institution makes the event operational?
3. What public benefit does that institution sincerely claim?
4. What allocation, authority, or continuity consequence follows?
5. Which existing game surface expresses it: Headline, Escalation, faction,
   tile, action, Era card, or ending?
6. Does the event preserve the printed mechanic, or does it propose a rule
   change requiring separate evidence and approval?

## World Ending direction

The current rules resolve four mechanical World Endings using two independent
axes: AGI emergence and Open/Closed continuity. AGI emergence requires the
shared five-percent gate to open and the fourth-power Mandate resolution to
select one institution. Open continuity requires collective Trust to improve
by the player count from setup and unresolved Systemic Risk to remain below the
player count.

| | Open Continuity | Closed Continuity |
| --- | --- | --- |
| AGI emerges | The Singularity: recursive technological change transforms civilization while living society retains standing to contest its direction. | The Closed Loop: genuine AGI exists, but its goals and successor institutions close over human disagreement. |
| AGI does not emerge | The Plural Future: material security and pluralism endure without a singular intelligence taking authority. | The Assured Continuity: automated institutions continue an unanswerable delivery ritual without requiring genuine AGI. |

The moral distinction is not simple optimism versus pessimism. It is whether
living people retain standing to contest, redirect, and participate in the
future. Collective Trust is the total across all players; an Open ending does
not require every institution to improve its own Trust independently.

## Writing contract

- Use sober, administrative language. Let the institutional framing create the
  pressure.
- Positive corporate language should conceal rather than announce loss of
  power: “generally available,” “provisioned,” “successfully scaled,” and
  “assured” are model forms.
- Keep factual claims fictional unless a real-world reference is explicitly
  presented as research input outside player copy.
- Do not use real people, companies, logos, copied trade dress, or recognizable
  caricatures.
- Do not use first-person torment, voyeuristic suffering, or body horror.
- Do not introduce a mechanical rule through flavor text.
- Do not use months or years in player-facing narrative copy.
- Use Arabic digits in card rules, costs, quantities, thresholds, tables,
  versions, and other operational references. Spell out ordinary whole numbers
  in narrative and explanatory prose when they are not operational.
- Exact component text remains exact wherever it is quoted or projected; the
  content compiler must not apply a spell-out filter.

## Review checklist

- Does the object belong to its Era rather than merely containing a striking
  science-fiction idea?
- Does it show a credible institutional path from benefit to consequence?
- Does the public-facing language sound positive, responsible, and plausible?
- Is the actual human loss of power implied through procedure rather than
  villainy?
- Does it map to an existing game surface and preserve its printed mechanic?
- Does it avoid unused or hidden copy in the content system?
