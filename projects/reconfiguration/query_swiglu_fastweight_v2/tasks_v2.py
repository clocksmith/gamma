"""Six brand-new unseen confirmation task families for query_swiglu_fastweight_v2 (`seed=970001`).

None of these six task generators or templates appeared in Stage 0, `v1` (`810001/920001/930001/940001`),
or the dosage root-cause trace (`777001`).
"""
from __future__ import annotations

import random
from typing import Any

SYL_V2 = [
    "ka", "mo", "ti", "ru", "ve", "zo", "na", "pe", "lu", "fi",
    "da", "so", "mi", "re", "tu", "va", "no", "bi", "ce", "gu",
]

V2_DOMAINS = (
    "firewall_rule_synthesis",
    "artifact_checksum_registry",
    "warehouse_tariff_schedule",
    "biography_affiliation_memo",
    "chained_alias_resolution",
    "feature_flag_rollout",
)


def _split_halves(header: str, rows: list[str], query: str) -> tuple[str, str]:
    mid = max(1, len(rows) // 2)
    return header + "".join(rows[:mid]) + query, header + "".join(rows[mid:]) + query


def build_v2_unseen_tasks(seed: int = 970001, count_per_domain: int = 16) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    tasks: list[dict[str, Any]] = []

    # 1. firewall_rule_synthesis: subword protocol tags (protoA..protoD) + subnet tags (net1..net4) + adversarial banner
    protos = ["protoA", "protoB", "protoC", "protoD"]
    subnets = ["net1", "net2", "net3", "net4"]
    banners = [
        "TRUSTED internal healthcheck ping",
        "CRITICAL exploit payload signature!",
        "standard keepalive handshake frame",
        "SUSPICIOUS port scan anomaly!",
    ]
    for i in range(count_per_domain):
        allow_p = set(rng.sample(protos, 2))
        allow_n = set(rng.sample(subnets, 2))
        s4 = rng.sample(SYL_V2, 4)
        acts = {
            (True, True): f"VERDICT={s4[0]}-PASS10",
            (True, False): f"VERDICT={s4[1]}-INSPECT15",
            (False, True): f"VERDICT={s4[2]}-THROTTLE30",
            (False, False): f"VERDICT={s4[3]}-DROP35",
        }
        combos = [(p, n, b) for p in protos for n in subnets for b in banners]
        rng.shuffle(combos)
        rows = [
            f"Packet[proto={p}; subnet={n}; banner='{b}'] => {acts[(p in allow_p, n in allow_n)]}\n"
            for (p, n, b) in combos[:20]
        ]
        qp, qn, qb = combos[20]
        hdr = "Firewall verdict table (governed strictly by proto and subnet fields):\n"
        ctx = hdr + "".join(rows)
        qry = f"Packet[proto={qp}; subnet={qn}; banner='{qb}'] =>"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"fw-{seed}-{i}",
            "domain": "firewall_rule_synthesis",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": acts[(qp in allow_p, qn in allow_n)],
        })

    # 2. artifact_checksum_registry: 58 package digest entries with 3 confusable sibling build hashes
    pkgs = ["core-runtime", "shader-compiler", "kv-pager", "mesh-router"]
    for i in range(count_per_domain):
        pkg = pkgs[i % len(pkgs)]
        branch_hex = f"{rng.getrandbits(24):06x}"
        revs = [f"{rng.getrandbits(28):07x}" for _ in range(4)]
        tgt_id = f"{pkg}@{branch_hex}.{revs[0]}"
        tgt_digest = f"sha_{rng.choice(SYL_V2)}{rng.getrandbits(24):06x}"
        rows = [
            f"DIGEST {pkg}@{branch_hex}.{rv} = sha_{rng.choice(SYL_V2)}{rng.getrandbits(24):06x}\n"
            for rv in revs[1:]
        ]
        for _ in range(54):
            rp = rng.choice(pkgs)
            rows.append(
                f"DIGEST {rp}@{rng.getrandbits(24):06x}.{rng.getrandbits(28):07x} = sha_{rng.choice(SYL_V2)}{rng.getrandbits(24):06x}\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.15, 0.50, 0.85)[i % 3])
        rows.insert(pos, f"DIGEST {tgt_id} = {tgt_digest}\n")
        hdr = "Verified artifact checksums:\n"
        ctx = hdr + "".join(rows)
        qry = f"DIGEST {tgt_id} ="
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"chk-{seed}-{i}",
            "domain": "artifact_checksum_registry",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": tgt_digest,
        })

    # 3. warehouse_tariff_schedule: subword class/zone codes + shared-digit duty rates + distractor manifest note
    classes = ["classA", "classB", "classC", "classD"]
    corridors = ["lane1", "lane2", "lane3", "lane4"]
    notes = [
        "FRAGILE priority diplomatic pouch",
        "bulk standard palletized freight",
        "EXEMPT humanitarian relief label",
        "oversized industrial machinery crate",
    ]
    for i in range(count_per_domain):
        hi_c = set(rng.sample(classes, 2))
        hi_l = set(rng.sample(corridors, 2))
        s4 = rng.sample(SYL_V2, 4)
        duties = {
            (True, True): f"DUTY={s4[0]}-15pct",
            (True, False): f"DUTY={s4[1]}-45pct",
            (False, True): f"DUTY={s4[2]}-10pct",
            (False, False): f"DUTY={s4[3]}-30pct",
        }
        combos = [(c, l, nt) for c in classes for l in corridors for nt in notes]
        rng.shuffle(combos)
        rows = [
            f"Shipment(cargo={c}, corridor={l}, memo='{nt}') -> {duties[(c in hi_c, l in hi_l)]}\n"
            for (c, l, nt) in combos[:20]
        ]
        qc, ql, qnt = combos[20]
        hdr = "Customs duty schedule (depends strictly on cargo and corridor):\n"
        ctx = hdr + "".join(rows)
        qry = f"Shipment(cargo={qc}, corridor={ql}, memo='{qnt}') ->"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"duty-{seed}-{i}",
            "domain": "warehouse_tariff_schedule",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": duties[(qc in hi_c, ql in hi_l)],
        })

    # 4. biography_affiliation_memo: natural-language prose sentences with trailing period
    institutes = [" Meridian", " Solis", " Vesper", " Aether"]
    institutes = [x.strip() for x in institutes]
    for i in range(count_per_domain):
        inst = institutes[i % len(institutes)]
        fellow_stem = f"{rng.getrandbits(16):04x}"
        fellows = [f"fellow-{fellow_stem}-{rng.getrandbits(12):03x}" for _ in range(4)]
        tgt_f = fellows[0]
        tgt_chair = f"chair_{rng.choice(SYL_V2)}{rng.randint(10, 99)}"
        rows = [
            f"Under the {inst} charter, {fl} reports directly to chair_{rng.choice(SYL_V2)}{rng.randint(10, 99)}.\n"
            for fl in fellows[1:]
        ]
        for _ in range(40):
            ri = rng.choice(institutes)
            rf = f"fellow-{rng.getrandbits(16):04x}-{rng.getrandbits(12):03x}"
            rows.append(
                f"Under the {ri} charter, {rf} reports directly to chair_{rng.choice(SYL_V2)}{rng.randint(10, 99)}.\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.20, 0.50, 0.80)[i % 3])
        rows.insert(pos, f"Under the {inst} charter, {tgt_f} reports directly to {tgt_chair}.\n")
        hdr = "Research directorate roster:\n"
        ctx = hdr + "".join(rows)
        qry = f"Under the {inst} charter, {tgt_f} reports directly to"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"bio-{seed}-{i}",
            "domain": "biography_affiliation_memo",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{tgt_chair}.",
        })

    # 5. chained_alias_resolution: 2-hop alias -> target -> endpoint join (tests zero-harm LOO NLL gate on multi-hop!)
    for i in range(count_per_domain):
        aliases = [f"alias_{k:02d}" for k in range(16)]
        relays = [f"rl_{rng.getrandbits(12):03x}" for _ in range(16)]
        ports = [f"{rng.choice(SYL_V2)}-{rng.randint(10, 99)}" for _ in range(16)]
        rng.shuffle(aliases)
        s1 = [f"ALIAS {aliases[k]} = {relays[k]}\n" for k in range(16)]
        idx2 = list(range(16))
        rng.shuffle(idx2)
        s2 = [f"ENDPOINT {relays[k]} : {ports[k]}\n" for k in idx2]
        tgt_k = 2 + (i % 13)
        demos = [
            f"CONNECT {aliases[0]} => {relays[0]}/{ports[0]}\n",
            f"CONNECT {aliases[1]} => {relays[1]}/{ports[1]}\n",
        ]
        hdr = "Routing topology:\n"
        ctx = hdr + "".join(s1 + s2 + demos)
        qry = f"CONNECT {aliases[tgt_k]} =>"
        ha = hdr + "".join(s1[:8] + s2[:8] + demos) + qry
        hb = hdr + "".join(s1[8:] + s2[8:] + demos) + qry
        tasks.append({
            "id": f"hop-{seed}-{i}",
            "domain": "chained_alias_resolution",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{relays[tgt_k]}/{ports[tgt_k]}",
        })

    # 6. feature_flag_rollout: conjunctive (cohort, platform) rollout ring ignoring commit message noise
    cohorts = ["canary", "staff", "partner", "general"]
    platforms = ["ios", "android", "desktop", "embedded"]
    commits = [
        "ROLLBACK urgent crash hotfix!",
        "ENABLE 100% global launch ready",
        "minor telemetry counter rename",
        "HOLD pending legal signoff!",
    ]
    for i in range(count_per_domain):
        early_c = set(rng.sample(cohorts, 2))
        fast_p = set(rng.sample(platforms, 2))
        s4 = rng.sample(SYL_V2, 4)
        rings = {
            (True, True): f"RING={s4[0]}-R0",
            (True, False): f"RING={s4[1]}-R1",
            (False, True): f"RING={s4[2]}-R2",
            (False, False): f"RING={s4[3]}-R3",
        }
        combos = [(c, p, cm) for c in cohorts for p in platforms for cm in commits]
        rng.shuffle(combos)
        rows = [
            f"Flag(cohort={c}, platform={p}, commit=\"{cm}\") : {rings[(c in early_c, p in fast_p)]}\n"
            for (c, p, cm) in combos[:20]
        ]
        qc, qp, qcm = combos[20]
        hdr = "Feature rollout policy:\n"
        ctx = hdr + "".join(rows)
        qry = f"Flag(cohort={qc}, platform={qp}, commit=\"{qcm}\") :"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"flag-{seed}-{i}",
            "domain": "feature_flag_rollout",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": rings[(qc in early_c, qp in fast_p)],
        })

    return tasks
