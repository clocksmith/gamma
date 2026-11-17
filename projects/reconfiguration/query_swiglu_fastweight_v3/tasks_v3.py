"""Six unseen application & compositional confirmation task families for FastWeight v3 (`seed=990001`).

Covers realistic developer/ops workloads alongside subword conjunctive rules and 2-hop composition:
1. `env_dotenv_secret_lookup`: `.env` / ConfigMap environment variable overrides with confusable sibling keys
2. `git_codeowners_routing`: Monorepo CODEOWNERS reviewer & risk-tier rule ignoring PR title noise
3. `service_dependency_twohop`: 2-hop `UPSTREAM -> mesh_id` + `HEALTH mesh_id : state` -> `PROBE => mesh_id/state`
4. `incident_postmortem_prose`: SRE incident postmortem prose sentences with trailing period
5. `sql_shard_policy_matrix`: Subword database shard (`shardA..D`) x isolation (`level1..4`) routing policy
6. `openapi_endpoint_rate_ledger`: OpenAPI route rate-limit spec registry with sibling tenant paths
"""
from __future__ import annotations

import random
from typing import Any

SYL_V3 = [
    "ka", "mo", "ti", "ru", "ve", "zo", "na", "pe", "lu", "fi",
    "da", "so", "mi", "re", "tu", "va", "no", "bi", "ce", "gu",
]

V3_DOMAINS = (
    "env_dotenv_secret_lookup",
    "git_codeowners_routing",
    "service_dependency_twohop",
    "incident_postmortem_prose",
    "sql_shard_policy_matrix",
    "openapi_endpoint_rate_ledger",
)


def _split_halves(header: str, rows: list[str], query: str) -> tuple[str, str]:
    mid = max(1, len(rows) // 2)
    return header + "".join(rows[:mid]) + query, header + "".join(rows[mid:]) + query


def build_v3_unseen_tasks(seed: int = 990001, count_per_domain: int = 16) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    tasks: list[dict[str, Any]] = []

    # 1. env_dotenv_secret_lookup: 56 .env service config entries with 3 confusable sibling keys
    prefixes = ["AUTH_JWT_SIGNER", "DB_REPLICA_DSN", "QUEUE_BROKER_URI", "CACHE_REDIS_POOL"]
    for i in range(count_per_domain):
        pfx = prefixes[i % len(prefixes)]
        cluster = f"C{rng.getrandbits(20):05x}".upper()
        shards = [f"S{rng.getrandbits(24):06x}".upper() for _ in range(4)]
        tgt_k = f"{pfx}_{cluster}_{shards[0]}"
        tgt_v = f"val_{rng.choice(SYL_V3)}_{rng.getrandbits(24):06x}"
        rows = [
            f"EXPORT {pfx}_{cluster}_{sh}={f'val_{rng.choice(SYL_V3)}_{rng.getrandbits(24):06x}'}\n"
            for sh in shards[1:]
        ]
        for _ in range(52):
            rp = rng.choice(prefixes)
            rows.append(
                f"EXPORT {rp}_C{rng.getrandbits(20):05x}_S{rng.getrandbits(24):06x}=val_{rng.choice(SYL_V3)}_{rng.getrandbits(24):06x}\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.15, 0.50, 0.85)[i % 3])
        rows.insert(pos, f"EXPORT {tgt_k}={tgt_v}\n")
        hdr = "# Production Kubernetes ConfigMap environment dump\n"
        ctx = hdr + "".join(rows)
        qry = f"EXPORT {tgt_k}="
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"env-{seed}-{i}",
            "domain": "env_dotenv_secret_lookup",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": tgt_v,
        })

    # 2. git_codeowners_routing: monorepo subsystem x blast_radius policy ignoring noisy PR title
    subsystems = ["kernel", "scheduler", "allocator", "tokenizer"]
    scopes = ["patch", "minor", "schema", "breaking"]
    titles = [
        "URGENT revert production outage!",
        "trivial typo fix in docs only",
        "ROUTINE weekly dependency bump",
        "SECURITY hotfix bypass requested!",
    ]
    for i in range(count_per_domain):
        core_sub = set(rng.sample(subsystems, 2))
        high_sc = set(rng.sample(scopes, 2))
        s4 = rng.sample(SYL_V3, 4)
        gates = {
            (True, True): f"GATE={s4[0]}-DUAL_SIGNOFF",
            (True, False): f"GATE={s4[1]}-OWNER_REVIEW",
            (False, True): f"GATE={s4[2]}-CANARY_REQ",
            (False, False): f"GATE={s4[3]}-AUTO_MERGE",
        }
        combos = [(sb, sc, tt) for sb in subsystems for sc in scopes for tt in titles]
        rng.shuffle(combos)
        rows = [
            f"PR(area={sb}, scope={sc}, title=\"{tt}\") => {gates[(sb in core_sub, sc in high_sc)]}\n"
            for (sb, sc, tt) in combos[:24]
        ]
        qsb, qsc, qtt = combos[24]
        hdr = "Repository merge-gate audit log (governed strictly by area and scope):\n"
        ctx = hdr + "".join(rows)
        qry = f"PR(area={qsb}, scope={qsc}, title=\"{qtt}\") =>"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"own-{seed}-{i}",
            "domain": "git_codeowners_routing",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": gates[(qsb in core_sub, qsc in high_sc)],
        })

    # 3. service_dependency_twohop: 2-hop UPSTREAM svc = mesh_id + HEALTH mesh_id : state -> PROBE svc => mesh_id/state
    for i in range(count_per_domain):
        svcs = [f"svc_{k:02d}" for k in range(16)]
        meshes = [f"msh_{rng.getrandbits(12):03x}" for _ in range(16)]
        states = [f"{rng.choice(SYL_V3)}-{rng.randint(10, 99)}" for _ in range(16)]
        rng.shuffle(svcs)
        s1 = [f"UPSTREAM {svcs[k]} = {meshes[k]}\n" for k in range(16)]
        idx2 = list(range(16))
        rng.shuffle(idx2)
        s2 = [f"HEALTH {meshes[k]} : {states[k]}\n" for k in idx2]
        tgt_k = 2 + (i % 13)
        demos = [
            f"PROBE {svcs[0]} => {meshes[0]}/{states[0]}\n",
            f"PROBE {svcs[1]} => {meshes[1]}/{states[1]}\n",
        ]
        hdr = "Service mesh dependency graph:\n"
        ctx = hdr + "".join(s1 + s2 + demos)
        qry = f"PROBE {svcs[tgt_k]} =>"
        ha = hdr + "".join(s1[:8] + s2[:8] + demos) + qry
        hb = hdr + "".join(s1[8:] + s2[8:] + demos) + qry
        tasks.append({
            "id": f"dep-{seed}-{i}",
            "domain": "service_dependency_twohop",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{meshes[tgt_k]}/{states[tgt_k]}",
        })

    # 4. incident_postmortem_prose: SRE postmortem sentences with trailing period
    regions = ["us-east", "eu-central", "ap-south", "us-west"]
    for i in range(count_per_domain):
        reg = regions[i % len(regions)]
        inc_stem = f"{rng.getrandbits(16):04x}"
        incs = [f"INC-{inc_stem}-{rng.getrandbits(12):03x}" for _ in range(4)]
        tgt_inc = incs[0]
        tgt_eng = f"oncall_{rng.choice(SYL_V3)}{rng.randint(10, 99)}"
        rows = [
            f"In region {reg}, outage {ic} was mitigated by oncall_{rng.choice(SYL_V3)}{rng.randint(10, 99)}.\n"
            for ic in incs[1:]
        ]
        for _ in range(40):
            rr = rng.choice(regions)
            ri = f"INC-{rng.getrandbits(16):04x}-{rng.getrandbits(12):03x}"
            rows.append(
                f"In region {rr}, outage {ri} was mitigated by oncall_{rng.choice(SYL_V3)}{rng.randint(10, 99)}.\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.20, 0.50, 0.80)[i % 3])
        rows.insert(pos, f"In region {reg}, outage {tgt_inc} was mitigated by {tgt_eng}.\n")
        hdr = "Quarterly reliability postmortem ledger:\n"
        ctx = hdr + "".join(rows)
        qry = f"In region {reg}, outage {tgt_inc} was mitigated by"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"inc-{seed}-{i}",
            "domain": "incident_postmortem_prose",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": f"{tgt_eng}.",
        })

    # 5. sql_shard_policy_matrix: subword shardA..D x level1..4 with shared-digit pool budgets
    shards_l = ["shardA", "shardB", "shardC", "shardD"]
    levels_l = ["level1", "level2", "level3", "level4"]
    hints = [
        "FORCE primary read-write override",
        "analytics background batch scan",
        "LOW_LATENCY checkout query hint",
        "archive cold-storage reporting",
    ]
    for i in range(count_per_domain):
        hot_s = set(rng.sample(shards_l, 2))
        strict_l = set(rng.sample(levels_l, 2))
        s4 = rng.sample(SYL_V3, 4)
        pools = {
            (True, True): f"POOL={s4[0]}-15conn",
            (True, False): f"POOL={s4[1]}-45conn",
            (False, True): f"POOL={s4[2]}-10conn",
            (False, False): f"POOL={s4[3]}-30conn",
        }
        combos = [(sh, lv, ht) for sh in shards_l for lv in levels_l for ht in hints]
        rng.shuffle(combos)
        rows = [
            f"Query[shard={sh}; iso={lv}; comment='{ht}'] -> {pools[(sh in hot_s, lv in strict_l)]}\n"
            for (sh, lv, ht) in combos[:24]
        ]
        qsh, qlv, qht = combos[24]
        hdr = "Database router pool table (depends strictly on shard and iso):\n"
        ctx = hdr + "".join(rows)
        qry = f"Query[shard={qsh}; iso={qlv}; comment='{qht}'] ->"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"sql-{seed}-{i}",
            "domain": "sql_shard_policy_matrix",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": pools[(qsh in hot_s, qlv in strict_l)],
        })

    # 6. openapi_endpoint_rate_ledger: 54 OpenAPI route rate-limit entries with sibling tenant IDs
    verbs = ["POST /v2/infer", "GET /v2/embeddings", "PUT /v2/checkpoints", "DELETE /v2/sessions"]
    for i in range(count_per_domain):
        vb = verbs[i % len(verbs)]
        org = f"org-{rng.getrandbits(20):05x}"
        apps = [f"app-{rng.getrandbits(24):06x}" for _ in range(4)]
        tgt_route = f"{vb}/{org}/{apps[0]}"
        tgt_lim = f"rpm_{rng.choice(SYL_V3)}_{rng.randint(100, 999)}"
        rows = [
            f"ROUTE {vb}/{org}/{ap} : rpm_{rng.choice(SYL_V3)}_{rng.randint(100, 999)}\n"
            for ap in apps[1:]
        ]
        for _ in range(50):
            rv = rng.choice(verbs)
            rows.append(
                f"ROUTE {rv}/org-{rng.getrandbits(20):05x}/app-{rng.getrandbits(24):06x} : rpm_{rng.choice(SYL_V3)}_{rng.randint(100, 999)}\n"
            )
        rng.shuffle(rows)
        pos = round(len(rows) * (0.15, 0.50, 0.85)[i % 3])
        rows.insert(pos, f"ROUTE {tgt_route} : {tgt_lim}\n")
        hdr = "OpenAPI gateway rate-limit table:\n"
        ctx = hdr + "".join(rows)
        qry = f"ROUTE {tgt_route} :"
        ha, hb = _split_halves(hdr, rows, qry)
        tasks.append({
            "id": f"api-{seed}-{i}",
            "domain": "openapi_endpoint_rate_ledger",
            "context_text": ctx,
            "query_text": qry,
            "prompt": ctx + qry,
            "half_a_prompt": ha,
            "half_b_prompt": hb,
            "expected": tgt_lim,
        })

    return tasks
