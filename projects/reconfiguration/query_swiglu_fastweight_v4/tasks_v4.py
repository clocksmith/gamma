"""Unseen non-copy semantic and compositional task suite for Track B1 v4 (`query_swiglu_fastweight_v4`).

All six domains are strictly disjoint from `v1`, `v2`, and `v3`:
1. `semantic_clinical_specialty_triage` (single-token arbitrary wing codes)
2. `paraphrased_cloud_incident_routing` (single-token arbitrary pager queues)
3. `latent_financial_compliance_desk` (single-token arbitrary desk codes)
4. `scientific_instrument_calibration` (single-token arbitrary bay labels)
5. `compositional_supply_hazard_codes` (multi-token hyphenated hazard codes)
6. `multilingual_civic_service_dispatch` (multi-token slash-delimited sector codes)

Design invariants:
- Support lines (`m = 12` per specialty, `3` per latent category) and unseen queries (`8` per specialty,
  `2` per latent category) draw from strictly disjoint phrase pools with orthogonal surface distractors,
  so lexical/BM25/regex lookup (`regex_baseline_v4.py`) scores near the `25%` 4-class chance level (`<= 50%`).
- Each domain instantiates two specialties (`spec_a`, `spec_b`) with distinct/permuted code assignments,
  enabling `wrong_specialty_lora` and A -> B -> revert hot-swap controls on identical query distributions.
"""
from __future__ import annotations

import random

V4_DOMAINS: tuple[str, ...] = (
    "semantic_clinical_specialty_triage",
    "paraphrased_cloud_incident_routing",
    "latent_financial_compliance_desk",
    "scientific_instrument_calibration",
    "compositional_supply_hazard_codes",
    "multilingual_civic_service_dispatch",
)

_DOMAIN_SPECS: dict[str, dict] = {
    "semantic_clinical_specialty_triage": {
        "header": "Assign each patient intake note to its clinic wing:\n",
        "prefix": "Intake",
        "tags": ("[ADULT]", "[PEDIATRIC]"),
        "codes_a": ("amber", "cobalt", "crimson", "silver"),
        "codes_b": ("ivory", "jade", "bronze", "coral"),
        "classes": (
            (
                "palpitations with irregular pulse during stair climbing",
                "substernal chest tightness radiating toward left jaw",
                "systolic murmur audible over aortic valve auscultation",
                "bradycardia episodes recorded on wearable electrocardiogram",
                "orthopnea requiring three pillows with ankle edema",
                "atrial flutter paroxysms following caffeine intake",
                "hypertensive blood pressure spike with bounding carotid pulse",
            ),
            (
                "unilateral visual aura preceding throbbing hemicranial migraine",
                "transient numbness and tingling across ulnar fingers",
                "resting tremor in dominant hand with cogwheel rigidity",
                "episodic vertigo with horizontal nystagmus on head turn",
                "expressive word-finding aphasia lasting ten minutes",
                "absent Achilles tendon reflex with distal foot drop",
                " nocturnal generalized tonic seizure witnessed by spouse",
            ),
            (
                "pruritic erythematous plaques with silvery scales on elbows",
                "vesicular rash following unilateral thoracic dermatome",
                "asymmetrical pigmented mole showing irregular scalloped border",
                "annular targetoid macule expanding after woodland hike",
                "chronic perioral pustules aggravated by topical ointment",
                "urticarial wheals appearing rapidly after shellfish meal",
                "subungual hyperkeratosis with brittle ridged fingernails",
            ),
            (
                "audible meniscus click and knee locking during squat",
                "rotator cuff weakness when abducting shoulder above ninety degrees",
                "plantar heel pain sharpest on first morning footsteps",
                "displaced distal radius fracture after fall on icy sidewalk",
                "lumbar facet stiffness worsening with spinal extension",
                "lateral epicondyle tenderness triggered by wrist supination",
                "achilles tendon swelling and crepitus after marathon training",
            ),
        ),
    },
    "paraphrased_cloud_incident_routing": {
        "header": "Route each telemetry alert to its on-call squad:\n",
        "prefix": "Alert",
        "tags": ("[PROD]", "[STAGE]"),
        "codes_a": ("maple", "cedar", "birch", "willow"),
        "codes_b": ("oak", "pine", "ash", "elm"),
        "classes": (
            (
                "write-ahead log compaction stalled behind locked row transactions",
                "read replica lag exceeding ninety seconds on primary shard",
                "foreign key deadlock aborting concurrent checkout commits",
                "b-tree index page split saturating storage iops queue",
                "vacuum autoworker blocked by orphaned snapshot cursor",
                "connection pool exhausted waiting for serializable isolation",
                "corrupted tablespace checksum detected during nightly backup",
            ),
            (
                "expired intermediate x509 authority rejecting mutual handshake",
                "oauth refresh bearer signature failing jwks rotation check",
                "saml assertion clock skew exceeding five minute tolerance",
                "revoked client hardware token denied bypkix responder",
                "mismatched subject alternative hostname on ingress cipher",
                "kerberos ticket granting renewal rejected by realm kdc",
                "hmac webhook digest mismatch after secret vault rollover",
            ),
            (
                "anycast bgp session flapping across transatlantic peering link",
                "authoritative nameserver returning nxdomain for internal zone",
                "asymmetric ECMP return path dropping jumbo ethernet frames",
                "nat gateway ephemeral port table reaching full exhaustion",
                "vxlan overlayarp broadcast storm flooding spine switches",
                "stale route reflector prefix hijacking regional subnet traffic",
                "mtu blackhole silently discarding fragmented gre tunnel packets",
            ),
            (
                "cuda allocator out-of-memory killing tensor worker process",
                "garbage collector stop-the-world pause exceeding twelve seconds",
                "unbounded Arenaslab fragmentation tripping cgroup oom-killer",
                "pinned host pagefile thrashing under kv-cache spill pressure",
                "leaked websocket bytebuffers growing resident set monotonically",
                "shared shmget segment hitting kernel ipc memory ceiling",
                "hugepage allocation failure stalling numa node initialization",
            ),
        ),
    },
    "latent_financial_compliance_desk": {
        "header": "Direct each surveillance filing to its review desk:\n",
        "prefix": "Filing",
        "tags": ("[Q1]", "[Q4]"),
        "codes_a": ("north", "south", "east", "west"),
        "codes_b": ("alpha", "beta", "gamma", "delta"),
        "classes": (
            (
                "executive option purchases executed hours before merger press release",
                "analyst research draft leaked to hedge fund prior to publication",
                "board member liquidating equity ahead of clinical trial halt",
                "unscheduled blackout-window share transfer by subsidiary treasurer",
                "correlated call-spread accumulation preceding earnings guidance cut",
                "procurement director buying supplier stock before contract award",
                "confidential tender valuation shared over unarchived personal chat",
            ),
            (
                "swift correspondent wire routed through embargoed maritime port",
                "shell beneficiary matching blocked sovereign entity watch list",
                "layered crypto-to-fiat structuring just below reporting threshold",
                "dual-use avionics invoice settled via third-country intermediary",
                "charitablewire transfer destined for sanctioned regional bank",
                "forged bill of lading obscuring restricted crude oil origin",
                "nominee director concealing politically exposed beneficial owner",
            ),
            (
                "missing nonresident dividend treaty form on cross-border payout",
                "backup withholding omitted from uncertified contractor disbursement",
                "transfer pricing royalty markup diverging from OECD arm-length band",
                "wash-sale cost basis disallowed on repurchased municipal bonds",
                "foreign permanent establishment payroll nexus unreported on return",
                "value-added reverse charge misclassified on digital SaaS invoices",
                "depreciation recapture schedule omitted after equipment disposal",
            ),
            (
                "intraday variation margin deficit breaching prime broker haircut",
                "rehypothecated sovereign repo collateral falling below maintenance",
                "concentrated short gamma portfolio failing stress-testvar limit",
                "cross-currency swap mark-to-market triggering credit support call",
                "illiquid high-yield bond pledge exceeding issuer concentration cap",
                "clearinghouse initial margin shortfall forcing automatic position trim",
                "unhedged delta exposure violating overnight desk mandate",
            ),
        ),
    },
    "scientific_instrument_calibration": {
        "header": "Dispatch each laboratory fault to its service bay:\n",
        "prefix": "Fault",
        "tags": ("[SHIFT-A]", "[SHIFT-B]"),
        "codes_a": ("harbor", "summit", "canyon", "meadow"),
        "codes_b": ("ridge", "valley", "basin", "plateau"),
        "classes": (
            (
                "turbomolecular backing pump failing to hold high-vacuum millitorr",
                "quadrupole electrospray capillary clogged by crystallized buffer salt",
                "electron multiplier detector gain drifting on m/z calibration peaks",
                "ion funnel rf amplitude arcing inside foreline chamber",
                "collision cell argon pressure fluctuating during tandem fragmentation",
                "time-of-flight reflectron voltage ripple broadening isotope envelope",
                "heated transfer capillary thermocouple reading open circuit",
            ),
            (
                "liquid helium boil-off rate doubling inside superconducting dewar",
                "deuterium lock channel losing field-frequency phase stability",
                "shim coil Z2 gradient current saturating spectral line width",
                "cryoprobe preamplifier thermal noise spiking above baseline",
                "quench heater safety interlock tripping magnet power supply",
                "magic-angle spinning zirconia stator stalling pneumatics bearing",
                "nitrogen cold-trap frost obstructing cryostat vent manifold",
            ),
            (
                "argon-krypton excitation beam misaligned from pinhole aperture",
                "piezo objective nanopositioner exhibiting hysteresis during z-stack",
                "photomultiplier dark counts surging from ambient light leak",
                "dichroic mirror coating delamination attenuating fluorescence emission",
                "galvanometer scan mirror ringing at high frame line rates",
                "immersion oil refractive mismatch blurring point-spread airy rings",
                "acousto-optic tunable filter drifting off 488nm wavelength",
            ),
            (
                "titanium fixed-angle rotor vibrating violently past 15000 rpm",
                "imbalanced polycarbonate tubes triggering shaft tachometershutdown",
                "refrigerated chamber compressor failing to maintain four celsius",
                "brushless spindle bearing whining during deceleration ramp",
                "vacuum lid elastomer gasket leaking aerosol containment seal",
                "swinging-bucket trunnion grease dry-out causing asymmetric tilt",
                "overspeed optical disk sensor covered by condensation film",
            ),
        ),
    },
    "compositional_supply_hazard_codes": {
        "header": "Label each manifest item with its storage bay code:\n",
        "prefix": "Manifest",
        "tags": ("[AIR]", "[SEA]"),
        "codes_a": ("red-1", "blue-2", "green-3", "gold-4"),
        "codes_b": ("blue-1", "gold-2", "red-3", "green-4"),
        "classes": (
            (
                "palletized lithium-ion pouch cells packed withperchlorate oxidizer",
                "pressurized acetylene cylinders alongside volatile ketone drums",
                "sodium metal ingots immersed in mineral oil hazard crates",
                "organic peroxide initiator vials requiring vented blast locker",
                "pyrophoric silane gas canisters fitted with brass check valves",
                "concentrated nitric acid carboys segregated from organic solvents",
                "aerosol propellant cans marked flammable Class 2.1",
            ),
            (
                "monoclonal antibody vials packed under sublimating dry ice pellets",
                "cryopreserved umbilical stem cells in vapor-phase nitrogen shipper",
                "live attenuated viral vaccine lots requiring minus-eighty freezer",
                "lyophilized enzyme reagents with continuous cold-chain datalogger",
                "donor corneal tissue media buffered at two to eight celsius",
                "thaw-sensitive mRNA lipid nanoparticles in phase-change cooler",
                "human plasma cryoprecipitate bags monitored for thermal excursion",
            ),
            (
                "interferometric fused-silica mirrors mounted on pneumatic shock skids",
                "wafer lithography reticle pellicles sealed in cleanroom nitrogen pod",
                "calibrated quartz crystal microbalances with tilt-watch indicators",
                "astronomical CCD focal plane array in electrostatic Faraday case",
                "hand-blown borosilicate distillation columns cushioned in foam",
                "fiber-optic gyroscope spools sensitive to axial G-force impact",
                "precision coordinate ruby stylus probes in fitted velvet tray",
            ),
            (
                "kiln-dried malting barley sacks fumigated for weevil quarantine",
                "raw arabica parchment coffee beans in breathable burlap totes",
                "certified non-gmo soybean planting seed in moisture-barrier bags",
                "milled durum semolina flour stored in food-grade silo hoppers",
                "dehulled sunflower kernels purged with inert nitrogen headspace",
                "pelleted alfalfa livestock forage wrapped against mold spoilage",
                "heirloom winter wheat grain sampled for aflatoxin screening",
            ),
        ),
    },
    "multilingual_civic_service_dispatch": {
        "header": "Dispatch each municipal report to its sector unit:\n",
        "prefix": "Report",
        "tags": ("[DAY]", "[NIGHT]"),
        "codes_a": ("north/1", "south/2", "east/3", "west/4"),
        "codes_b": ("west/1", "north/2", "south/3", "east/4"),
        "classes": (
            (
                "ruptured cast-iron aqueduct flooding downtown intersection pavement",
                "fuga de agua potable brotando bajo la acera residencial",
                "hydrant standpipe sheared off by delivery truck gushing onto street",
                "canalisation principale cassee inondant le sous-sol municipal",
                "sinkhole opening above corroded storm sewer culvert pipe",
                "baja presion severa por tuberia matriz reventada en avenida",
                "backflow preventer valve bursting inside park pump station",
            ),
            (
                "pole-mounted distribution transformer arcing sparks during drizzle",
                "apagon total de alumbrado publico en cuatro cuadras del barrio",
                "downed overhead primary conductor energizing wet chain-link fence",
                "panne de lampadaires urbains apres court-circuit du transformateur",
                "flickering crosswalk signal dark after underground feeder fault",
                "cables electricos caidos bloqueando la entrada de la escuela",
                "substation breaker lockout plunging pedestrian tunnel into darkness",
            ),
            (
                "uprooted sycamore trunk blocking both northbound commuter lanes",
                "arbol caido por vendaval obstruyendo completamente la calzada",
                "shattered oak limb dangling precariously over sidewalk bike path",
                "grand platane deracine fermant la route departementale",
                "mudslide boulders and snapped pine branches covering mountain curve",
                "ramas pesadas quebradas impidiendo el paso de ambulancias",
                "windblown willow canopy across tramway catenary tracks",
            ),
            (
                "overflowing curbside blue recycling bins skipped for two weeks",
                "contenedores de basura organica sin recoger desde el martes",
                "illegal mattress and drywall dumping piled behind alley dumpster",
                "collecte des dechets menagers oubliee dans toute la rue",
                "broken municipal compactor truck leaving bags scattered on curb",
                "acumulacion de residuos reciclables vidrio y carton en esquina",
                "missed municipal compost pickup attracting raccoons on boulevard",
            ),
        ),
    },
}


def build_v4_unseen_tasks(
    seed: int = 1040001,
    queries_per_specialty: int = 8,
) -> list[dict]:
    """Build deterministic Track B1 v4 unseen tasks (`6` domains x `2` specialties x `queries_per_specialty`)."""
    if seed < 1040000:
        raise ValueError(f"Confirmation seed must be >= 1040000 to prevent dev/eval overlap (got {seed}).")
    if queries_per_specialty < 1 or queries_per_specialty > 8:
        raise ValueError(f"queries_per_specialty must be in 1..8 (got {queries_per_specialty}).")

    rng = random.Random(seed)
    tasks: list[dict] = []
    task_id = 0

    for dom in V4_DOMAINS:
        spec_cfg = _DOMAIN_SPECS[dom]
        header = spec_cfg["header"]
        prefix = spec_cfg["prefix"]
        tags = spec_cfg["tags"]
        classes = spec_cfg["classes"]

        # Partition each 7-item class pool into 3 support phrases + 2 query_a phrases + 2 query_b phrases
        # (`3 + 2 = 5 <= 7`, strictly disjoint phrases between support and queries!)
        per_class_pools = []
        for cls_phrases in classes:
            shuffled = list(cls_phrases)
            rng.shuffle(shuffled)
            per_class_pools.append({
                "sup_a": shuffled[0:3],
                "qry_a": shuffled[3:5],
                "sup_b": shuffled[2:5],
                "qry_b": [shuffled[5], shuffled[6]],
            })

        spec_pair = [
            (f"{dom}__spec_a", f"{dom}__spec_b", spec_cfg["codes_a"], "sup_a", "qry_a"),
            (f"{dom}__spec_b", f"{dom}__spec_a", spec_cfg["codes_b"], "sup_b", "qry_b"),
        ]

        for spec_id, wrong_spec_id, codes, sup_key, qry_key in spec_pair:
            support_lines: list[str] = []
            for round_idx in range(3):
                order = [0, 1, 2, 3]
                rng.shuffle(order)
                for c_idx in order:
                    phrase = per_class_pools[c_idx][sup_key][round_idx]
                    # Balance surface tags orthogonally across classes
                    tag = tags[(c_idx + round_idx) % len(tags)]
                    support_lines.append(f"{prefix}: {tag} {phrase} => {codes[c_idx]}\n")

            support_text = header + "".join(support_lines)

            query_candidates: list[tuple[str, str]] = []
            for q_round in range(2):
                for c_idx in range(4):
                    q_phrase = per_class_pools[c_idx][qry_key][q_round]
                    # Adversarial tag flip relative to support round 0 so surface tags have 0 predictive value
                    q_tag = tags[(c_idx + q_round + 1) % len(tags)]
                    query_line = f"{prefix}: {q_tag} {q_phrase} =>"
                    query_candidates.append((query_line, codes[c_idx]))

            for query_line, expected in query_candidates[:queries_per_specialty]:
                tasks.append({
                    "task_id": task_id,
                    "domain": dom,
                    "specialty_id": spec_id,
                    "wrong_specialty_id": wrong_spec_id,
                    "header_text": header,
                    "support_text": support_text,
                    "query_line": query_line,
                    "bare_prompt": header + query_line,
                    "prompt": support_text + query_line,
                    "expected": expected,
                    "max_new_tokens": 5,
                })
                task_id += 1

    return tasks
