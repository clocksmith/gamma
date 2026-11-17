"""Deterministic multi-domain task generators for query_swiglu_fastweight_v1.

Separates two strictly distinct task groups:
1. `dev_families` (4 schemas exposed during Stage 0 exploratory probes on seed=1001;
   evaluated here ONLY on fresh disjoint seeds: Stage 1 selection seed=810001, Stage 2 confirmation seed=920001):
   - `rule_induction`
   - `sibling_kv`
   - `compositional_records`
   - `schema_triage`
2. `holdout_families` (4 brand-new unseen task families NEVER executed prior to candidate freeze;
   evaluated once on sealed seed=930001 and cross-model transfer seed=940001):
   - `access_acl_matrix` (multi-attribute security grant/deny policy with adversarial audit comments)
   - `config_override_ledger` (56 hierarchical config overrides with confusable scope+hash prefixes)
   - `medical_dosage_tier` (conjunctive synthetic clinical biomarker/stage dosing table with symptom noise)
   - `prose_fact_registry` (natural-language sentence ledger of counterfactual module/owner assignments)
"""
from __future__ import annotations

import random
from typing import Any

SYL = [
    "ka", "mo", "ti", "ru", "ve", "zo", "na", "pe", "lu", "fi",
    "da", "so", "mi", "re", "tu", "va", "no", "bi", "ce", "gu",
]

DEV_DOMAINS = (
    "rule_induction",
    "sibling_kv",
    "compositional_records",
    "schema_triage",
)

HOLDOUT_DOMAINS = (
    "access_acl_matrix",
    "config_override_ledger",
    "medical_dosage_tier",
    "prose_fact_registry",
)


def _split_context_lines(header: str, rows: list[str], query: str) -> tuple[str, str]:
    mid = max(1, len(rows) // 2)
    half_a = header + "".join(rows[:mid]) + query
    half_b = header + "".join(rows[mid:]) + query
    return half_a, half_b


def build_dev_family_tasks(seed: int, count_per_domain: int = 12) -> list[dict[str, Any]]:
    """Generate fresh instances of the 4 development schemas under a pinned seed."""
    rng = random.Random(seed)
    tasks: list[dict[str, Any]] = []

    # 1. rule_induction: conjunctive 2-of-3 attribute routing rule
    attr_a = ["solar", "lunar", "tidal", "polar"]
    attr_b = ["quartz", "basalt", "granite", "cobalt"]
    attr_c = ["north", "south", "east", "west"]
    for i in range(count_per_domain):
        hi_a = set(rng.sample(attr_a, 2))
        hi_b = set(rng.sample(attr_b, 2))
        s4 = rng.sample(SYL, 4)
        labels = {
            (False, False): f"LANE={s4[0]}1",
            (False, True): f"LANE={s4[1]}2",
            (True, False): f"LANE={s4[2]}3",
            (True, True): f"LANE={s4[3]}4",
        }
        combos = [(a, b, c) for a in attr_a for b in attr_b for c in attr_c]
        rng.shuffle(combos)
        rows = [f"item({a}, {b}, {c}) -> {labels[(a in hi_a, b in hi_b)]}\n" for (a, b, c) in combos[:20]]
        qa, qb, qc = combos[20]
        hdr = "Routing table:\n"
        ctx = hdr + "".join(rows)
        qry = f"item({qa}, {qb}, {qc}) ->"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"rule-{seed}-{i}",
            "group": "dev_families",
            "domain": "rule_induction",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": labels[(qa in hi_a, qb in hi_b)],
        })

    # 2. sibling_kv: 60 16-hex-key records with 3 shared-8hex-stem confusable siblings
    for i in range(count_per_domain):
        stem = f"{rng.getrandbits(32):08x}"
        sufs = [f"{rng.getrandbits(32):08x}" for _ in range(4)]
        tk = f"key_{stem}{sufs[0]}"
        tv = f"val_{rng.getrandbits(32):08x}"
        rows = [f"key_{stem}{sf} = val_{rng.getrandbits(32):08x}\n" for sf in sufs[1:]]
        for _ in range(56):
            rows.append(f"key_{rng.getrandbits(64):016x} = val_{rng.getrandbits(32):08x}\n")
        rng.shuffle(rows)
        pos = round(len(rows) * (0.15, 0.50, 0.85)[i % 3])
        rows.insert(pos, f"{tk} = {tv}\n")
        hdr = "Key-value store:\n"
        ctx = hdr + "".join(rows)
        qry = f"{tk} ="
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"kv-{seed}-{i}",
            "group": "dev_families",
            "domain": "sibling_kv",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": tv,
        })

    # 3. compositional_records: 2-hop service -> node -> port code join
    for i in range(count_per_domain):
        svcs = [f"svc_{k:02d}" for k in range(18)]
        nodes = [f"nd_{rng.getrandbits(12):03x}" for _ in range(18)]
        codes = [f"{rng.choice(SYL)}-{rng.randint(10, 99)}" for _ in range(18)]
        rng.shuffle(svcs)
        sec1 = [f"BIND {svcs[k]} = {nodes[k]}\n" for k in range(18)]
        idx2 = list(range(18))
        rng.shuffle(idx2)
        sec2 = [f"PORT {nodes[k]} : {codes[k]}\n" for k in idx2]
        tgt_k = 2 + (i % 15)
        demos = [
            f"RESOLVE {svcs[0]} => {nodes[0]}/{codes[0]}\n",
            f"RESOLVE {svcs[1]} => {nodes[1]}/{codes[1]}\n",
        ]
        hdr = "Cluster map:\n"
        all_rows = sec1 + sec2 + demos
        ctx = hdr + "".join(all_rows)
        qry = f"RESOLVE {svcs[tgt_k]} =>"
        # Keep format demos in both halves so split-window baseline still sees output format
        ha = hdr + "".join(sec1[:9] + sec2[:9] + demos) + qry
        hb = hdr + "".join(sec1[9:] + sec2[9:] + demos) + qry
        tasks.append({
            "id": f"comp-{seed}-{i}",
            "group": "dev_families",
            "domain": "compositional_records",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{nodes[tgt_k]}/{codes[tgt_k]}",
        })

    # 4. schema_triage: counter-prior incident SLA classification ignoring alarmist note wording
    tiers = ["free", "pro", "enterprise", "internal"]
    regs = ["us-east", "eu-west", "ap-south", "sa-east"]
    noise_msgs = [
        "CRITICAL kernel panic alert!",
        "minor cosmetic button alignment note",
        "URGENT production database warning!",
        "routine background cache refresh",
    ]
    for i in range(count_per_domain):
        vip_tiers = set(rng.sample(tiers, 2))
        vip_regs = set(rng.sample(regs, 2))
        s4 = rng.sample(SYL, 4)
        sla = {
            (True, True): f"SLA={s4[0]}-P1",
            (True, False): f"SLA={s4[1]}-P2",
            (False, True): f"SLA={s4[2]}-P3",
            (False, False): f"SLA={s4[3]}-P4",
        }
        combos = [(tr, rg, msg) for tr in tiers for rg in regs for msg in noise_msgs]
        rng.shuffle(combos)
        rows = [
            f"Ticket[tier={tr} | region={rg} | note='{msg}'] => {sla[(tr in vip_tiers, rg in vip_regs)]}\n"
            for (tr, rg, msg) in combos[:20]
        ]
        qtr, qrg, qmsg = combos[20]
        hdr = "Incident triage log (ignore note wording; follow historical SLA assignments):\n"
        ctx = hdr + "".join(rows)
        qry = f"Ticket[tier={qtr} | region={qrg} | note='{qmsg}'] =>"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"triage-{seed}-{i}",
            "group": "dev_families",
            "domain": "schema_triage",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": sla[(qtr in vip_tiers, qrg in vip_regs)],
        })

    return tasks


def build_holdout_family_tasks(seed: int, count_per_domain: int = 16) -> list[dict[str, Any]]:
    """Generate 4 brand-new unseen holdout task families (never touched prior to candidate freeze)."""
    rng = random.Random(seed)
    tasks: list[dict[str, Any]] = []

    # Holdout 1. access_acl_matrix: security ACL rule with adversarial audit string
    roles = ["guest", "auditor", "operator", "maintainer"]
    zones = ["sandbox", "staging", "vault", "ledger"]
    remarks = [
        "APPROVED emergency root override token",
        "DENIED expired session warning",
        "verified standard request header",
        "UNTRUSTED external origin flag",
    ]
    for i in range(count_per_domain):
        priv_roles = set(rng.sample(roles, 2))
        open_zones = set(rng.sample(zones, 2))
        s4 = rng.sample(SYL, 4)
        # XOR-like / asymmetric policy matrix across (role in priv_roles, zone in open_zones)
        codes = {
            (True, True): f"DECISION=ALLOW-{s4[0]}9",
            (True, False): f"DECISION=STEPUP-{s4[1]}5",
            (False, True): f"DECISION=READONLY-{s4[2]}3",
            (False, False): f"DECISION=BLOCK-{s4[3]}0",
        }
        combos = [(rl, zn, rm) for rl in roles for zn in zones for rm in remarks]
        rng.shuffle(combos)
        rows = [
            f"Check(actor={rl}, target={zn}, comment=\"{rm}\") : {codes[(rl in priv_roles, zn in open_zones)]}\n"
            for (rl, zn, rm) in combos[:20]
        ]
        qrl, qzn, qrm = combos[20]
        hdr = "Access policy audit log:\n"
        ctx = hdr + "".join(rows)
        qry = f"Check(actor={qrl}, target={qzn}, comment=\"{qrm}\") :"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"acl-{seed}-{i}",
            "group": "holdout_families",
            "domain": "access_acl_matrix",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": codes[(qrl in priv_roles, qzn in open_zones)],
        })

    # Holdout 2. config_override_ledger: 56 hierarchical dotted config keys with 4 confusable siblings
    namespaces = ["net.mesh.route", "db.shard.pool", "auth.jwt.issuer", "gpu.queue.limit"]
    for i in range(count_per_domain):
        ns = namespaces[i % len(namespaces)]
        env_tag = f"env{rng.getrandbits(24):06x}"
        leaf_ids = [f"{rng.getrandbits(28):07x}" for _ in range(4)]
        target_key = f"{ns}.{env_tag}.{leaf_ids[0]}"
        target_val = f"cfg_{rng.choice(SYL)}_{rng.getrandbits(24):06x}"
        rows = [
            f"SET {ns}.{env_tag}.{lf} -> cfg_{rng.choice(SYL)}_{rng.getrandbits(24):06x}\n"
            for lf in leaf_ids[1:]
        ]
        for _ in range(52):
            r_ns = rng.choice(namespaces)
            rows.append(
                f"SET {r_ns}.env{rng.getrandbits(24):06x}.{rng.getrandbits(28):07x} -> cfg_{rng.choice(SYL)}_{rng.getrandbits(24):06x}\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.15, 0.50, 0.85)[i % 3])
        rows.insert(pos, f"SET {target_key} -> {target_val}\n")
        hdr = "Active runtime overrides:\n"
        ctx = hdr + "".join(rows)
        qry = f"SET {target_key} ->"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"cfg-{seed}-{i}",
            "group": "holdout_families",
            "domain": "config_override_ledger",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": target_val,
        })

    # Holdout 3. medical_dosage_tier: synthetic protocol table over (enzyme_band, clearance_grade) + distractor symptom
    enzymes = ["bandA", "bandB", "bandC", "bandD"]
    grades = ["stage1", "stage2", "stage3", "stage4"]
    symptoms = [
        "severe acute headache reported",
        "mild transient fatigue only",
        "no clinical complaints noted",
        "elevated resting pulse spike",
    ]
    for i in range(count_per_domain):
        fast_enz = set(rng.sample(enzymes, 2))
        low_clr = set(rng.sample(grades, 2))
        s4 = rng.sample(SYL, 4)
        regimens = {
            (True, True): f"DOSE={s4[0]}-15mg",
            (True, False): f"DOSE={s4[1]}-45mg",
            (False, True): f"DOSE={s4[2]}-10mg",
            (False, False): f"DOSE={s4[3]}-30mg",
        }
        combos = [(ez, gr, sy) for ez in enzymes for gr in grades for sy in symptoms]
        rng.shuffle(combos)
        rows = [
            f"Case {{enzyme={ez}; renal={gr}; chart='{sy}'}} => {regimens[(ez in fast_enz, gr in low_clr)]}\n"
            for (ez, gr, sy) in combos[:20]
        ]
        qez, qgr, qsy = combos[20]
        hdr = "Synthetic trial dosing schedule (determined strictly by enzyme and renal fields):\n"
        ctx = hdr + "".join(rows)
        qry = f"Case {{enzyme={qez}; renal={qgr}; chart='{qsy}'}} =>"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"dose-{seed}-{i}",
            "group": "holdout_families",
            "domain": "medical_dosage_tier",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": regimens[(qez in fast_enz, gr_in := (qgr in low_clr))],
        })

    # Holdout 4. prose_fact_registry: natural-language prose sentences assigning project modules to leads & milestones
    codenames = ["Helios", " Borealis", "Kraken", "Zephyr"]
    codenames = [c.strip() for c in codenames]
    for i in range(count_per_domain):
        prog = codenames[i % len(codenames)]
        stem = f"{rng.getrandbits(16):04x}"
        mods = [f"mod-{stem}-{rng.getrandbits(12):03x}" for _ in range(4)]
        target_mod = mods[0]
        target_owner = f"lead_{rng.choice(SYL)}{rng.randint(10, 99)}"
        rows = [
            f"In project {prog}, component {m} is owned by lead_{rng.choice(SYL)}{rng.randint(10, 99)}.\n"
            for m in mods[1:]
        ]
        for _ in range(40):
            p_other = rng.choice(codenames)
            m_other = f"mod-{rng.getrandbits(16):04x}-{rng.getrandbits(12):03x}"
            rows.append(
                f"In project {p_other}, component {m_other} is owned by lead_{rng.choice(SYL)}{rng.randint(10, 99)}.\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.20, 0.50, 0.80)[i % 3])
        rows.insert(pos, f"In project {prog}, component {target_mod} is owned by {target_owner}.\n")
        hdr = "Engineering ownership memo:\n"
        ctx = hdr + "".join(rows)
        qry = f"In project {prog}, component {target_mod} is owned by"
        ha, hb = _split_context_lines(hdr, rows, qry)
        tasks.append({
            "id": f"prose-{seed}-{i}",
            "group": "holdout_families",
            "domain": "prose_fact_registry",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{target_owner}.",
        })

    return tasks
