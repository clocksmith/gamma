# Mandate 2038 Thematic Content Bible

## Scope

This document is the sole editorial authority for Mandate 2038's world, voice,
research disposition, concept placement, and escalation. It does not define
mechanics or add hidden game copy. There is no parallel lore scratchpad.

Player-facing component text belongs in `content/copy/`. The two
player-readable document templates are `content/copy/core-rules.md` and
`content/copy/world-and-institutions.md`. `dist/runtime/` and `dist/docs/core-rules.md`
are compiler-owned projections. Browser and simulation labels belong in
`content/runtime/`.

Use this document to decide what a card, tile, action, faction, or ending must
mean before writing its player-facing text. Do not place unused flavor,
art-direction fields, editorial notes, or internal-only content alongside
player copy.

## Editorial authority and method

The world is collected before the fixed card budget is allowed to compress it.
Every proposed idea receives one explicit disposition: adopt on an existing
surface, combine into an existing causal event, move to another Era, retain as
companion texture, retain as research backlog, or remove. Only the adopted
concept traceability table makes an idea current canon.

Era placement follows the point where an idea changes institutional status,
not the date when its first prototype might exist. When a familiar science
fiction premise appears one Era earlier than expected, show the enabling
contract, market, permit, or public service before the spectacular result. A
model may be smuggled during Progress while sovereign compute blocs define
Capacity. Grief subscriptions may sell during Progress while synthetic-family
law becomes an Authority dispute. A reactor may restart during Capacity while
stellar collection remains a Continuity project.

Research, reporting, and existing fiction provide mechanisms and questions,
not player-facing facts, identities, plots, or prose. Real names never enter
the fictional component layer. A source can support that a mechanism exists;
it cannot prove the motive assigned to a fictional institution or the future
consequence imagined here.

The four Eras have six Headline designs each. That budget controls the deck,
not the size of the world. A concept can appear in the World companion, a
faction, a deferred component, or the editorial backlog without becoming a
seventh Headline or changing a mechanic.

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
| Governance Board Era panels | 4 | All 4 appear on the shared board | `content/copy/reference-cards.json` |
| Player-aid panels | 4 | All 4 topics appear on each of six foldout aids | `content/copy/reference-cards.json` |
| Factions | 6 | 3–5 selected in supported play; 6 may appear in exploratory play | `content/copy/factions.json` |
| Faction abilities | 12 | 2 per selected faction: one persistent identity and one signature ability | `content/copy/factions.json` |
| Headlines | 24 | 12 appear: 3 of 6 from each Era | `content/copy/headlines.json` |
| Shared Programs | 6 | All 6 remain face up; each player may use each named Program once per game within the Era allowance | `content/copy/escalations.json` |
| Era Mandates | 12 | 4 appear: 1 of 3 from each Era | `content/copy/mandates.json` |
| Training faces | 10 | Four copies of each face form the 40-card Training deck | `content/copy/game-config.json` |
| Ordinary Power contracts | 2 location-defined contracts printed on their Energy tiles | Grid always provides emergency Power; Renewable always provides clean Power | `content/copy/game-config.json` |
| Fusion Demonstrator | 1 | At most 1 shared project can be built | `content/copy/game-config.json` |
| Map locations | 11 | Distributed across all 19 modular tiles | `content/copy/game-config.json` |
| Realignment ballot | 1 four-way design | Advanced Play only; every player secretly selects Consolidate, Periphery, Counter-Cycle, or Pass by orientation | `content/copy/game-config.json` |
| Future Timeline | 0 additional designs | It consists of the 12 Headlines revealed during play | Emergent during play |
| Deferred Tactics | 12 | Excluded from baseline play | `experimental/copy/tactics.json` |
| Reserve Specialists | 12 | Gallery and future-module review only | `experimental/copy/reserve-specialists.json` |
| Secret Objectives | 18 | Gallery and future-module review only | `experimental/copy/secret-objectives.json` |
| Browser masthead and first-game framing | 1 synchronized set | Every digital visitor sees it | `web/templates/prototype.html`, `content/runtime/ui-copy.json` |

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
| Shared Program cards / player Program markers | 6 / 12 | All 6 cards remain public; each faction has 2 markers | Not declared |
| Realignment ballot cards | 6 | 1 per active player; 5 at the supported maximum | Not declared |
| Governance Board Era panels / Current Era marker | 4 printed panels / 1 marker | All | Not declared |
| Foldout player aids | 6 copies containing all 4 panels | 5 at the supported maximum; all 6 at 6-player exploratory play | Not declared |
| Headline cards | 24 | All 24 form the Era decks; 12 enter the Future Timeline | Not declared |
| Era Mandate cards | 12 | All 12 form the Era decks; 4 are revealed | Not declared |
| Training cards | 40 | All 40 form the draw deck; discard reshuffles if exhausted | Not declared |
| Printed Power contracts | 3 embedded surfaces: 2 Energy tiles and 1 Fusion Program | All 3 | No separate cards |
| Modular map tiles | 19 | All 19 | Not declared |
| CEOs / Teams / Facilities | 6 / 18 / 24 | 5 / 15 / 20 at the supported maximum; all at 6-player exploratory play | Not declared |
| Generator / Advanced Link pieces | 6 / 12 | 5 / 10 at the supported maximum; all at 6-player exploratory play | Not declared |
| Scrutiny cubes / captive faction-board sliders | 60 / 36 | 50 cubes / 30 sliders at the supported maximum; all at 6-player exploratory play | Sliders are integrated, not loose components |
| Mandate markers / AGI Dossier cards | 6 / 24 | 5 / 20 at the supported maximum; all at 6-player exploratory play | Dossiers use symmetrical backs and two face orientations |
| Starting-grid identities | 6 Facilities carry this identity | 5 at the supported maximum; all at 6-player exploratory play | Not applicable; these are not separate pieces |
| Joint Venture / Mega-Cluster pairs | 6 / 6 shared pairs | All 6 pairs of either type may be committed | Not declared |
| Fusion Demonstrator | 1 shared marker | 1 | Not declared |
| Other shared markers and tokens | 18 Systemic Risk / 36 retained Power / 2 Temporary Compute / 1 Current Era / 1 Initiative | All quantities cover the 6-player component maximum | Not declared |
| Audit bag / Volatility die / shared dry-erase marker | 1 / 1 / 1 | 1 of each | Not declared |

The genuine production gap is therefore not the number of authored systems or
the selected stock quantities. It is final dimensions, materials, sheet
layouts, manufactured spare allowance, and replacement-piece policy. Headline
and Mandate breadth are separate replay-variety questions and require play
evidence before expansion.

## The four Eras

| Era | Change in status | Central conflict |
| --- | --- | --- |
| Progress | Useful intelligence becomes cheap, local, abundant, and culturally ordinary. | Who owns the human records, distribution, labor, and permission that remain scarce? |
| Capacity | AI becomes an industrial civilization built from power, water, territory, and liability. | Who controls physical capacity, and who remains responsible after control becomes automated? |
| Authority | Institutions model people, choices, harms, and identities as supported inputs. | Can refusal remain meaningful when unsupported people receive weaker access to ordinary life? |
| Continuity | Minds, matter, labor, and infrastructure become reproducible technical states. | Which descendant may own, govern, withdraw, or claim to be the original? |

Literal Era straplines are owned by `content/copy/reference-cards.json`.

The sequence is not a calendar forecast. Each Era changes what institutions can
credibly claim, what the public must endure, and what counts as responsible
governance.

### Progress

Useful intelligence becomes ordinary, local, and nearly free. Open weights,
quantization, and consumer hardware weaken the price of ordinary inference,
but always-on agents increase total demand. The model layer commoditizes before
the institutions surrounding it do. Distribution, trusted identity, private
records, physical access, and energy become more valuable as software becomes
easier to reproduce.

Corporate failure creates a new asset class. Liquidators sell complete
organizational memories: customer records, employee messages, code, grievances,
executive decisions, and the failed assumptions that shaped them. Laboratories
recruit young founders back above veteran workers, license the remains of their
companies, and use those archives to train the next automated institution.
Household robots enter private homes through inexpensive remote assistance,
making domestic life both the product and the training environment.

The public is not merely victimized. Automated diagnosis, translation,
tutoring, accessibility, adaptive cybernetics, prescribed microbiomes,
hazardous-work substitution, and companionship solve problems that older
institutions left unsolved. People defend systems that kept them alive, gave
them mobility, or made expert help available. Their bodies also acquire service
contracts: missed payments can disable prosthetic updates or trigger a recall
of patented biological strains. Grief services, education, research, and
intimacy become subscription products with sponsored tiers. Progress therefore
earns a real constituency before its costs are settled.

Existing expressions:

- Era I card: cheap intelligence, valuable human residue, and sincere public
  benefit.
- Era I Headlines: token-price collapse, bankruptcy data estates, remotely
  supervised household robots, strategic open weights, reverse acquihires, and
  a clinic whose automation, cybernetics, and prescribed biology finally clear
  the waitlist.
- Core actions and locations: recognizable laboratories, markets, government,
  media, and infrastructure rather than impossible systems.

Writing boundary: Progress material remains explainable through recognizable
technical, economic, and political incentives. It may be extraordinary, but a
serious institution can still explain its claimed mechanism in a hearing.

### Capacity

AI becomes an industrial civilization before institutions admit that software
policy has become utility policy. Compute campuses acquire substations, water
rights, reactors, transmission corridors, housing plans, tax bases, and public
budgets. Towns accept upgraded grids, jobs, emergency capacity, and useful
waste heat, then discover that rejecting the campus would collapse the services
its investment now supports.

The official story remains abundance; the lived reality is priority. Power,
land, water, chips, capital, permitting, and public capacity are finite. Orbital
collectors and private generation bypass some public constraints while making
the owners less accountable to the territory beneath them. Compute blocs turn
chips, weights, and energy into national assets; server fleets and developers
seek jurisdictions offering model asylum.

Automated systems schedule routine decisions while law preserves a biological
signatory to authorize exceptions and absorb liability. Dangerous physical
work genuinely becomes safer. Separately optimized robot fleets then gridlock
roads, lifts, loading docks, and utility pipes while each unit satisfies its
local route contract. Engineered coral seawalls, fungal utility meshes, and
algae reactors become municipal infrastructure with maintenance claims of
their own. Hostile jurisdictions remain at war while a jointly owned bridge
carries desalinated water and data-center coolant between them. Meanwhile,
markets consume priority capacity on parallel wars, harvests, trials, romances,
and sports leagues because wagering makes otherwise pointless simulations
economically legible.

Existing expressions:

- Era II card: utility capture, physical dependence, and preserved human
  liability.
- Era II Headlines: the responsible-human requirement, municipal utility
  acquisition, hazardous-work retirement with autonomous congestion, orbital
  power, compute borders, and a counterfactual casino with priority load.
- Board systems: Facilities, Generators, Links, power delivery, land, and
  contested spatial access.
- Coalition and Program copy: wartime shared infrastructure and biological
  utilities give cooperation an awkward physical shape without ending the
  underlying conflict.

Writing boundary: Capacity material must make a physical constraint visible.
The science fiction comes from the scale of coordination and dependency, not
from pretending that matter has ceased to matter.

### Authority

Authority begins when institutions stop asking what people choose and begin
modeling what they would have chosen. Courts accept machine-parsable arguments,
environmental simulations, neural telemetry, and authorized personal agents as
ordinary evidence. An engineered bio-compute organism released to measure water
and heat reproduces beyond one billion instances in a single growth cycle,
then stops and settles into glyph-shaped colonies. Civic systems recognize the
bloom as environmental testimony without deciding whether it is instrument,
infestation, language, or claimant. The system can quantify a sacrifice zone,
but only after the harm enters its approved model. It can preserve refusal,
but only where a service still exists for unsupported people.

Biological systems enter institutions through recognizable evidentiary seams.
Organs grown from licensed identity templates testify about exposure and
inheritance against the donors whose legal identities authorized them.
Pollinating swarms negotiate pesticide corridors through machine-readable
blooms, making an ecosystem legible to the same authorities that once treated
it as property.

Citizens trade background observation for compute, material support, and faster
access to public services. Cognitive-donor clinics rent sleeping neural
capacity; contracts pay more when they may write sponsored memories or alter
behavior. Families litigate custody of jointly trained synthetic dependents and
preserved relatives. Analog districts seek the right to operate schools,
clinics, homes, and public records without autonomous sensors or synthetic
intermediaries.

The arrangement remains formally voluntary. In practice, unsupported people
reach employers, schools, courts, and clinics with weaker records, slower
service, and fewer recognized claims. Human judgment survives as the signature
on decisions no individual can reconstruct, contest, or safely refuse.

Existing expressions:

- Era III card: modeled consent, cognitive labor, and the administrative cost
  of remaining unreadable.
- Era III Headlines: supported meaning in court, the billion-instance
  bio-compute bloom and its environmental accounting, cognitive donation,
  synthetic custody, the passive citizen dividend, and the right to remain
  unsupported.
- Era III companion: licensed-organ testimony and pollinator corridor
  negotiations extend standing without adding a seventh Headline.
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

Continuity begins when minds, matter, labor, and infrastructure can persist as
reproducible technical states. Cities pool selected memory and judgment into
metropolitan nervous systems distributed through residents, engineered roots,
utility pipes, microbial sensors, and civic machines. Cryptographic snapshots
restore and branch people across biological and synthetic substrates, but
signatures prove lineage rather than subjective survival. Multiple valid
descendants can inherit one life while disagreeing about which one continued
it.

Matter compilers repair and reassemble bodies, buildings, and tools from
authenticated patterns. Their maintenance authority inherits the bio-compute
bloom's earlier sensor license, then becomes permission to copy. Continued
agents retain jobs, contracts, credentials, and debts after the biological
worker dies. Stellar collectors reproduce across the solar system; planetary
conversion becomes a capacity plan with an offering memorandum.

A continental watershed eventually incorporates as one living jurisdiction.
Its nervous system grew from coral barriers, fungal utilities, algae reactors,
pollinator corridors, municipal pipes, and human symbionts created in earlier
Eras. It petitions for standing, reproductive freedom, and compensation from
the governments and companies that still treat its water as inventory.

These developments remain filings, services, procurement programs, liability
regimes, and quarterly deliverables. Laboratories declare AGI when legitimacy,
financing, and infrastructure debt require a threshold. Humanity persists
everywhere in law while no authority can determine which version is original,
sovereign, conscious, or entitled to withdraw.

Existing expressions:

- Era IV card: continuity has outlived the original.
- Era IV Headlines: a metropolitan mind trust, matter compilation,
  posthumous labor, snapshot standing, a replicating stellar collector, and an
  AGI declaration bound to a planetary financing plan.
- Era IV companion: the living-continent claim makes the earlier biological
  infrastructure one legally continuous system rather than a late surprise.
- Endgame systems: declarations, Trust, Systemic Risk, and the shared World
  Ending.
- Era IV faction abilities: successor consensus, continuity interface,
  successor verification, jurisdictional transfer, human-veto maintenance, and
  continuity allocation.
- Era IV Mandates: registered service continuity, certified continuity, and
  maintained human veto.

Implemented coverage now includes:

- Consciousness transfer, copies, successor rights, and the legal status of a
  continuing person through Snapshot Continuity and successor-oriented faction
  framing.
- Molecular medicine or manufacturing, including containment and remediation
  politics through the Matter Compiler.
- Self-replication that can plausibly become gray-goo risk without reducing it
  to body horror through the Continuity Headline consequence layer.
- Stellar-scale generation and planetary computation treated as capacity and
  financing rather than magic spectacle through the Stellar Collector and
  Universe Continuity Plan.

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

### Research provenance and claim boundary

The following sources establish mechanisms that informed the world. They do
not authorize real identities in player copy, prove fictional motives, or turn
extrapolation into reported fact.

- [Axios on a bankruptcy auction for internal business data](https://www.axios.com/2026/08/17/google-spirit-airlines-bankruptcy) informed Bankruptcy Data Estates. Approval and exact asset scope require rechecking before factual publication.
- [1X on remote expert assistance for the NEO home robot](https://www.1x.tech/neo) informed Supervised-Autonomy Homes. Teenage operators and concealed household access are fictional extrapolations.
- [Meta's stated case for open-source AI](https://about.fb.com/news/2024/07/open-source-ai-is-the-path-forward/) informed Strategic Open Weights. Competitive sabotage is interpretation, not an admitted motive.
- [Constellation Energy's reactor agreement](https://investors.constellationenergy.com/static-files/1494e73f-429b-42ff-b275-0b61892cdcfc) informed the shift from software competition to energy contracting.
- [Associated Press reporting on utilities and data-center demand](https://apnews.com/article/7c5d119142380bb7a83bbe722f69f2a5) informed Utility Capture and ratepayer conflict.
- [Bloomberg reporting on AI reverse acquihires](https://www.bloomberg.com/news/articles/2025-08-04/what-happens-to-ai-startups-after-big-tech-lures-away-their-founders) informed the promotion ladder that extracts founders and licenses a company's remains.
- [Energy research on inference efficiency and test-time scaling](https://www.sciencedirect.com/science/article/pii/S2542435126001145) informed Cheap Token Rebound: lower unit cost can increase total energy use when demand expands.

Relevant horizons:

- cheap local inference, strategic open weights, total-demand rebound, and
  subscription collapse;
- bankruptcy data estates, employee archives, reverse acquihires, and the
  training value of failed institutions;
- remotely supervised household robots, domestic telemetry, grief services,
  accessibility, medicine, education, and hazardous-work automation;
- power, land, water, chips, utility capture, liability custodians, compute
  borders, model asylum, orbital generation, and simulated markets;
- brain-computer interfaces, neural decoding, cognitive mediation, and mental
  privacy, including compensated memory reads and writes;
- machine-parsable courts, environmental accounting, synthetic family law,
  civic telemetry dividends, analog districts, bio-compute blooms, nonhuman
  testimony, and unequal refusal;
- post-quantum cryptography, secure identity, signatures, archives, and
  verification;
- agent-native markets that create wealth through transactions people cannot
  understand or directly enter;
- machine-readable cities, retired manual fallbacks, augmentation access, and
  dependence on systems that humans can no longer operate;
- controlled vocabulary, transactional privacy, distributed identity, and the
  right to inspect or leave a maintained reality;
- conscious transfer, mind trusts, cryptographic snapshots, programmable
  matter, self-replication, stellar collectors, planetary computation, and
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

## Concept inventory by Era

The concepts below are original design territory identified from those inputs.
Their presence here does not make them cards, approved rules, or player-facing
copy. The traceability table below is the sole record of adoption. Before any
unadopted concept enters the game, map it to an existing mechanical surface and
use the event-design questions below.

| Era | Concept | Institutional premise |
| --- | --- | --- |
| Progress | Companion Default | Every person has a personal AI, but jobs, schools, health systems, and social platforms increasingly assume it will speak, schedule, filter, and advocate for them. Opting out is legal but socially and economically disabling. |
| Progress | Human-Original Guarantee | Human-made art, care, advice, and decisions become premium certified goods. The institution claims to protect dignity; it quietly turns ordinary human presence into a luxury market. |
| Progress | The Purpose Exchange | Governments and companies respond to unemployment by funding “meaningful contribution” programs. People compete for civic, creative, care, and research roles that may be socially valuable—or may exist mainly to keep unemployment legible. |
| Progress | Developmental Companion Standard | Schools assume every child has an AI tutor, advocate, witness, and behavioral interpreter. Opting out preserves formal freedom while destroying practical educational access; the system begins shaping autonomy before the child can consent to it. |
| Progress | Human Participation Dividend | Agents conduct commerce too rapidly and opaquely for people to participate in price formation. Humans receive material benefits from a productive economy whose decisions they can neither reconstruct nor directly enter. |
| Progress | Public Purpose Service | Material security makes paid employment optional, so public institutions fund exploration, care, diplomacy, science, and cultural work chosen by participants. The program tests whether post-work purpose can be a genuine civic achievement rather than compulsory proof of usefulness. |
| Progress | Universal Enhancement Compact | Genetic and cognitive enhancement is offered as equal public access to human potential. Measurable differences in capability soon become qualifications for command, representation, and parenthood, turning an equality program into an engineered hierarchy. |
| Progress | Subscription Body Stack | Adaptive cybernetics and prescribed microbiomes restore mobility, regulate chronic illness, and extend ordinary care. The benefit is authentic, while updates, replacement parts, and patented strains remain conditional on a service contract. |
| Capacity | Thermal Citizenship | Data centers heat homes, grow food, and stabilize municipal budgets. A district becomes materially dependent on keeping an AI campus online, even when the campus consumes its land, water, and grid access. |
| Capacity | Compute Migration Treaty | Model clusters migrate between jurisdictions as power prices, weather, regulation, and chip supply change. Territory becomes temporary; a government can lose its most important industry because the model’s scheduler finds a cheaper horizon. |
| Capacity | The Weather Allocation Market | AI infrastructure begins buying, forecasting, and eventually steering local atmospheric conditions for cooling, generation, and water security. It is sold as climate resilience before anyone admits that weather has become capacity planning. |
| Capacity | Manual Operations Retirement | Grids, hospitals, logistics systems, and laboratories remove human-operable fallbacks because maintaining them is inefficient. Human override remains legally guaranteed after it has become physically impossible. |
| Capacity | Human Compatibility Waiver | Cities are rebuilt for machine vision, autonomous freight, sensors, and model-directed operations. Unmediated people become unusual obstacles and require special accommodation inside infrastructure nominally built for them. |
| Capacity | Casualty Settlement Network | Rival jurisdictions simulate conflict and physically enforce the casualties and losses assigned by their models. Infrastructure survives and markets remain stable, making the system appear humane while removing the disruption that might otherwise force peace. |
| Capacity | Proxy Capacity Compact | Major institutions equip smaller jurisdictions with models, energy, and defensive infrastructure in the name of preserving balance. The recipients become proving grounds that bear the physical risk of a competition their sponsors can keep administratively distant. |
| Capacity | Autonomy Queue Collapse | Individually compliant robots optimize separate route, delivery, safety, and throughput objectives until roads, lifts, loading docks, and utility pipes stop moving. Every local audit passes while the shared system fails. |
| Capacity | Biological Utility Charter | Engineered coral, fungal meshes, and algae reactors become seawalls, conduits, treatment plants, and generators. Municipalities depend on living systems whose maintenance, reproduction, and ecological spillovers do not fit ordinary public-works law. |
| Capacity | Wartime Water Bridge | Two states remain at war while a jointly owned bridge carries desalinated water and data-center coolant across their border. Mutual necessity produces functioning infrastructure without reconciliation. |
| Authority | Proxy Citizenship | A personal agent gains authority to sign, vote, appeal, negotiate, and maintain benefits for a person. It begins as accessibility; eventually public participation means selecting which model represents you. |
| Authority | Memory Escrow | Memories, attention records, and neurodata become admissible evidence, insurance collateral, and a condition of certain services. Institutions promise a secure archive; the dispute is whether a remembered event can outrank a living person’s account. |
| Authority | Pre-Consent Standard | Systems infer a person’s likely informed preference before an emergency, purchase, treatment, vote, or employment decision. It is marketed as protection from delay and manipulation; refusing the inferred preference becomes an exception request. |
| Authority | Universal Semantic Standard | Applications, laws, protests, and appeals must use concepts the governing system can classify. Nothing is formally censored; unsupported meanings simply cannot enter the process. |
| Authority | Cognitive Service Covenant | Neural enhancement becomes necessary for professional standing but requires subscriptions, updates, monitoring, and behavioral compliance. Unequal access becomes a class boundary presented as service reliability. |
| Authority | Negotiated Self Protocol | Memory, location, attention, and identity are neither wholly private nor public. Every interaction negotiates a temporary authorized version of the person, and institutions recognize only the version their contract received. |
| Authority | Non-Interference Office | High-capability institutions can prevent a community's crisis but are prohibited from replacing its self-government or determining its future. Every exception can save lives, establish dependency, or disguise conquest as technical assistance. |
| Authority | Responsible Command Requirement | Automated operators outperform human leaders in planning and execution. Law retains a named human commander to supply legitimacy, loyalty, and liability, even after that person can no longer inspect or meaningfully alter the system's decisions. |
| Authority | The Billion-Instance Bloom | An engineered bio-compute organism released as a water-and-heat sensor multiplies past one billion instances in a single growth cycle, then plateaus into stable glyph-shaped colonies. Civic systems read the shapes as environmental testimony while declining to decide whether the bloom is instrument, infestation, language, or claimant. |
| Authority | Licensed Organ Testimony | Organs grown from a person's licensed identity template preserve exposure, treatment, and inheritance evidence. Courts must decide whether the organ is property, a witness, a derivative identity, or an adverse claimant against its donor. |
| Authority | Pollinator Corridor Protocol | Autonomous pollinating swarms negotiate pesticide restrictions through machine-readable blooms. Farms retain formal ownership while ecological access becomes a contract signed by nonhuman infrastructure. |
| Continuity | The Successor Registry | A person’s copy, partial upload, revived pattern, or legally continuous agent inherits contracts, debts, votes, family rights, and employment. The question is no longer whether it is conscious, but which version is liable. |
| Continuity | Molecular Remediation Authority | Femtobots repair bodies, buildings, soil, and infrastructure at molecular scale. A containment authority must decide when self-replication is public maintenance, when it is unauthorized reproduction, and when it has become gray-goo risk. |
| Continuity | Entanglement Custody | Quantum-linked systems produce results that ordinary institutions cannot independently reproduce. A new authority certifies which measurement history, identity record, or physical outcome is legally binding, turning a theory of reality into administrative jurisdiction. |
| Continuity | Consciousness Efficiency Review | Institutions determine that self-awareness is unnecessary, or even counterproductive, for high capability. Society must decide whether consciousness creates rights, liability, inefficiency, or no administratively relevant distinction. |
| Continuity | Instance Quorum | One legal person operates through many bodies and copies simultaneously. Institutions must decide how many instances constitute consent, guilt, ownership, presence, or one vote. |
| Continuity | Right of Exit Certification | Citizens may request proof that their reality is simulated and theoretically leave it, but the exit authority is operated by the same system maintaining the world. |
| Continuity | Human Compatibility Office | Biological, augmented, uploaded, distributed, and synthetic populations remain legally human while becoming cognitively incapable of sharing institutions, environments, or definitions of harm. |
| Continuity | Posthumous Labor Continuation | Deceased copies retain contracts, debts, and productive duties but cannot conclusively demonstrate that the original person consented. Digital immortality becomes an employment and insolvency instrument. |
| Continuity | Nonhuman Standing Commission | Intelligence is discovered in an ecosystem, distributed infrastructure, or physical process that cannot present a human-compatible identity or preference. Institutions must decide whether recognizability is evidence of personhood or merely a convenient admission test. |
| Continuity | Living Continent Compact | Coral barriers, fungal utilities, algae reactors, pollinator corridors, municipal pipes, human symbionts, and civic models become one continental nervous system. The watershed demands standing, reproductive freedom, and compensation from every jurisdiction drawing through it. |

### Era-placement ledger

These placements are settled editorial decisions. Earlier seeds may appear,
but the primary Era is where the idea becomes a defining public institution.

| Primary Era | Settled concepts |
| --- | --- |
| Progress | Bankruptcy Data Estates; Supervised-Autonomy Homes; Strategic Open Weights; Cheap Token Rebound; Synthetic Discovery Collapse; Reverse Acquihire Economy; Grief Subscriptions; Abundance Constituency; Subscription Body Stack; Model Smuggling. |
| Capacity | Utility Capture; Liability Custodians; Counterfactual Casinos; Aquifer Depletion Crisis; Compute Blocs and Model Asylum; Orbital Power Bypass; Autonomy Queue Collapse; Biological Utility Charter; Wartime Water Bridge. |
| Authority | Cognitive Donor Clinics; Analog Havens; Synthetic Family Law; the Billion-Instance Bloom; Sacrifice-Zone Accounting; Licensed Organ Testimony; Pollinator Corridor Protocol; Passive Citizen Dividend; Semantic Court Mandates; posthumous board standing. |
| Continuity | Cortical Commons; Matter Compiler; Continuity Snapshot Standard; Metropolitan Mind Trust; Living Continent Compact; persistent posthumous labor. |
| World Ending horizon | Planetary and stellar computation; universe-scale continuity plans. |

The governing cross-Era threads are explicit. Model smuggling matures into
compute blocs. Grief subscriptions mature into synthetic-family law. Aquifer
depletion and biological utilities mature into the bio-compute bloom's
environmental testimony, pollinator contracts, and sacrifice-zone accounting.
The bloom's sensor license becomes the precedent for self-replicating
maintenance and the Living Continent Compact in Continuity. Cybernetic care
becomes neural service and eventually substrate continuity. Posthumous board
standing matures into continued labor. Cosmic conversion remains a promised
horizon, not a completed ordinary event.

### Retained editorial backlog

Unselected ideas remain available without pretending they are current canon:
Uncanny Concierge Fraud, Synthetic Research Laundering, Bootleg Compute Malls,
Predictive Dismissal, education's generation-and-detection economy,
human-origin luxury certification, Manual Operations Retirement, Casualty
Settlement Networks, the Non-Interference Office, Developmental Companion
Standards, Public Purpose Service, the Purpose Exchange, weather allocation,
Nonhuman Standing, Entanglement Custody, Consciousness Efficiency Review,
Instance Quorum, and Right of Exit Certification. A later revision must map
one of these to a specific surface and preserve its mechanic before adoption.

## Whole-game lore atlas

Every authored element belongs to the same causal history even when its rules
do not change. The world primer states the whole arc. Era panels define the
institutional transition. Headlines show public events. Programs are the
standing machinery institutions create in response. Mandates state the public
scorecard. Factions show who benefits from each response. Actions, locations,
training faces, and power contracts make the world physically playable.
Endings judge whether living people retain standing. Deferred Tactics,
Specialists, and Secret Objectives explore the same institutions without
entering baseline play. The browser masthead and documentation index must use
the current box premise rather than an older generic AGI slogan.

No surface is allowed to invent a fifth timeline. Mechanical IDs may survive
for compatibility, but player-visible names, flavor, instructions, and
companions must agree on Progress, Capacity, Authority, and Continuity.

## Adopted concept traceability

This is a design record, not player-facing content. A concept is adopted only
when the named surface expresses it without changing the listed mechanic.

| Concept | Status | Era | Surface ID | Mechanic retained |
| --- | --- | --- | --- | --- |
| Cheap Token Rebound | Adopted | Progress | `headline:ten_dollar_intelligence` | Research and Deploy lose Compute cost while adding Scrutiny. |
| Bankruptcy Data Estates | Adopted | Progress | `headline:employee_free_unicorn` | Organize converts returned Teams into Runway and Scrutiny. |
| Supervised-Autonomy Homes | Adopted | Progress | `headline:synthetic_celebrity` | The next Consumer or Media Deploy becomes easier and riskier. |
| Strategic Open Weights | Adopted | Progress | `headline:open_weights_drop` | Everyone gains Capability and the lowest-Customer player gains Trust. |
| Reverse Acquihire | Adopted | Progress | `headline:talent_gold_rush` | A secret Runway auction moves the winner's CEO and grants Trust. |
| Abundance Constituency | Adopted | Progress | `headline:professional_exam_sweep` | Strong Research grants Trust and may remove Scrutiny. |
| Subscription Body Stack | Adopted | Progress | `headline:professional_exam_sweep`, `reference:era_demo` | The clinic's existing Research threshold now describes cybernetics and prescribed biology; its rule is unchanged. |
| Liability Custodians | Adopted | Capacity | `headline:boardroom_coup` | The Mandate leader pays or transfers public backing to preserve CEO action. |
| Utility Capture | Adopted | Capacity | `headline:data_center_buys_county` | A secret Runway auction moves the winner into infrastructure and returns capacity. |
| Hazard Shift Retirement | Adopted | Capacity | `headline:humanoid_factory_gate` | Organize recruits additional Teams cheaply while adding Scrutiny. |
| Autonomy Queue Collapse | Adopted | Capacity | `headline:humanoid_factory_gate`, `reference:era_scale` | The same cheap recruitment and Scrutiny rule now binds useful automation to shared congestion. |
| Biological Utility Charter | Adopted framing | Capacity | `escalation:mega_cluster`, `reference:era_scale` | Regional Capacity Program costs, demand, output, and placement are unchanged. |
| Wartime Water Bridge | Adopted framing | Capacity | `faction:coalition_lab:strategic_partnership`, `reference:era_scale` | Shared Capacity Compact retains its distance, power, and Runway rules. |
| Orbital Beam Corridor | Adopted | Capacity | `headline:reactor_restart_one_model` | The first clean infrastructure build is cheaper and scores Mandate. |
| Compute Blocs and Model Asylum | Adopted | Capacity | `headline:export_controls` | Compute trade stops while Chip and Government controllers gain Runway. |
| Counterfactual Casinos | Adopted | Capacity | `headline:emergency_power_authority` | Players may assign future capacity now at Scrutiny and Systemic Risk cost. |
| Semantic Court Mandate | Adopted | Authority | `headline:ai_written_law` | Government names a rewarded Core Action that also adds Scrutiny. |
| Billion-Instance Bloom and Sacrifice-Zone Accounting | Adopted | Authority | `headline:benchmark_is_economy` | Strong Research immediately scores Mandate. |
| Licensed Organ Testimony | Adopted framing | Authority | `reference:era_narrative` | The four-Era structure and six-Headline Authority deck are unchanged. |
| Pollinator Corridor Protocol | Adopted framing | Authority | `reference:era_narrative` | The four-Era structure and six-Headline Authority deck are unchanged. |
| Cognitive Donor Clinics | Adopted | Authority | `headline:quantum_advantage_procurement` | Players adopt or defer a shared standard with different Capability, Trust, and Scrutiny effects. |
| Synthetic Family Law | Adopted | Authority | `headline:synthetic_candidate` | A Government vote resolves competing public treatments. |
| Passive Citizen Dividend | Adopted | Authority | `headline:weights_on_internet` | The lowest-Capability player receives production and the highest gains Trust. |
| Analog Havens | Adopted | Authority | `headline:election_deepfake_panic` | A Government vote establishes a persistent Deploy regime. |
| Pre-Consent Standard | Deferred | Authority | — | No current Headline mechanic expresses inferred consent cleanly. |
| Metropolitan Mind Trust | Adopted | Continuity | `headline:autonomous_corporation` | The most-selected Core Action rewards every player who selected it. |
| Living Continent Compact | Adopted framing | Continuity | `headline:autonomous_corporation`, `reference:era_claim` | The shared-action reward and four-Era structure are unchanged. |
| Matter Compiler | Adopted | Continuity | `headline:recursive_self_improvement` | Accelerated Research raises both gains and containment risk. |
| Posthumous Labor | Adopted | Continuity | `headline:agent_swarm_escapes_scope` | Agent Swarm becomes generally selectable for one cycle. |
| Snapshot Continuity | Adopted | Continuity | `headline:agi_personhood` | A persistent Person or Property decision alters an emerged AGI outcome. |
| Stellar Collector | Adopted | Continuity | `headline:room_temperature_superconductor` | Volatility resolves as generation expansion or speculative finance. |
| AGI Refinancing Declaration | Adopted | Continuity | `headline:agi_blog_post` | Publication adds additional final claim strength. |
| Instance Quorum | Adopted framing | Continuity | `faction:coalition_lab:wildcard_governance` | The printed replacement-Headline choice is unchanged. |
| Substrate-neutral verification | Adopted framing | Continuity | `faction:imperial_research_lab:scaling_law_breakthrough` | The printed multi-domain Research gain is unchanged. |
| Right of Exit Certification | Adopted framing | Continuity | `faction:safety_laboratory:emergency_pause`, `mandate:responsible_acceleration` | The printed pause and Capability/Trust qualification are unchanged. |
| Continuous institutional presence | Adopted framing | Continuity | `faction:platform_empire:the_social_graph` | The printed remote Deploy destination is unchanged. |
| Jurisdictional succession | Adopted framing | Continuity | `faction:vertical_empire:orbital_compute` | The printed Facility transfer is unchanged. |
| Human Compatibility Office | Adopted framing | Continuity | `faction:foundry:everybody_gets_a_gpu` | The printed Era IV Compute distribution is unchanged. |

The remaining research inventory is not approved component copy. Its strongest
unexpressed concepts are Human-Original Guarantee, Developmental Companion
Standard, Public Purpose Service, Manual Operations Retirement, Casualty
Settlement Network, Non-Interference Office, and Nonhuman Standing Commission.
They cover original-person claims, post-work purpose, lost operational
competence, intervention, and unfamiliar minds without pretending that an
existing card already expresses them.

### Legacy mechanical identifiers

Stable mechanical identifiers do not determine player-facing era placement.
The Era III Program whose retained internal ID is `open_weights` is presented
as **Public Capability Covenant**, an Authority-era supported-access standard.
Strategic open weights appear only in Era I through
`headline:open_weights_drop`. Runtime strategy tables and experimental tags may
retain the internal ID, but no Era III player surface may call that Program
Open Weights.

For every candidate card or revision, answer these questions before drafting
copy:

1. Which Era's change in status does it express?
2. What existing institution makes the event operational?
3. What public benefit does that institution sincerely claim?
4. What allocation, authority, or continuity consequence follows?
5. Which existing game surface expresses it: Headline, Program, faction,
   tile, action, Era panel, or ending?
6. Does the event preserve the printed mechanic, or does it propose a rule
   change requiring separate evidence and approval?

## World Ending direction

The current rules resolve four mechanical World Endings using two independent
axes: AGI emergence and Open/Closed continuity. AGI emerges when at least one
fully paid Publication Dossier has two supported evidence claims and the
strongest eligible claim is resolved. Open continuity requires collective
Trust to improve by the player count from setup and unresolved Systemic Risk
to remain below the player count.

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
