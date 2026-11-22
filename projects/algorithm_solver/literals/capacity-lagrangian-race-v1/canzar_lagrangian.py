#!/usr/bin/env python3
"""Canzar et al. (ALENEX 2012) shortest-path Lagrangian relaxation baseline for Minimum String Cover
under witness rule W_k (k >= 2, max_bytes = 160, whole programs excluded).

Avoids materializing any explicit LP matrix. Dualizes the linking constraints f_a <= x_{t(a)}
with multipliers lambda_a >= 0 projected onto the per-token simplex sum_{a in occ(t)} lambda_a <= 1,
evaluating L(lambda) = sum_b SP_b(lambda) by topological DAG shortest paths on deduplicated forced
blocks, updating multipliers via Held-Karp/Polyak subgradient ascent, and extracting:
  - IMPOSSIBLE: exact integer-scaled rational Fraction potential certificate checked independently
                over ALL arcs (zero floating-point trust);
  - FEASIBLE:   primal shortest-path dictionary (with greedy pruning) verified byte-exact by
                verify_construction;
  - Optional branch-and-bound / MILP fallback when subgradient stalls on undecided queries.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG_DIR = HERE.parent / "capacity-diagnostic-v1"
sys.path.insert(0, str(DIAG_DIR))

from diagnostic import (  # noqa: E402
    forced_blocks,
    parse_program,
    suffix_shared_lengths,
    verify_construction,
)


def _project_simplex_le_one(vals: list[float]) -> list[float]:
    """Euclidean projection of `vals` onto {x >= 0 : sum(x) <= 1}."""
    pos = [v if v > 0.0 else 0.0 for v in vals]
    s = sum(pos)
    if s <= 1.0:
        return pos
    # Standard Duchi et al. O(m log m) projection onto sum(x) == 1
    u = sorted(pos, reverse=True)
    cssv = 0.0
    rho = -1
    theta = 0.0
    for j, uj in enumerate(u):
        cssv += uj
        t = (cssv - 1.0) / (j + 1)
        if uj - t > 0.0:
            rho = j
            theta = t
    return [v - theta if v > theta else 0.0 for v in pos]


def build_block_dags(programs: list[str], k: int = 2, max_bytes: int = 160):
    """Build compact integer-indexed DAG adjacency lists on deduplicated forced blocks."""
    whole = set(programs)
    blocks = forced_blocks(programs, k, max_bytes=max_bytes)
    wit = suffix_shared_lengths(programs, k, max_bytes=max_bytes)

    elig_multi: set[str] = set()
    for pidx, s in enumerate(programs):
        row = wit[pidx]
        for a, w in enumerate(row):
            if w < 2:
                continue
            for b in range(a + 2, a + w + 1):
                sub = s[a:b]
                if sub not in whole:
                    elig_multi.add(sub)

    by_first: dict[str, list[str]] = defaultdict(list)
    for tok in elig_multi:
        by_first[tok[0]].append(tok)

    tok_to_id: dict[str, int] = {}
    id_to_tok: list[str] = []
    # Per block: out_arcs[i] = list of (arc_id, j, tid)
    block_dags: list[list[list[tuple[int, int, int]]]] = []
    arc_tid: list[int] = []
    tok_arcs: list[list[int]] = []
    arc_meta: list[tuple[int, int, int, int]] = []  # (bi, i, j, tid)

    def get_tid(tok: str) -> int:
        tid = tok_to_id.get(tok)
        if tid is None:
            tid = len(id_to_tok)
            tok_to_id[tok] = tid
            id_to_tok.append(tok)
            tok_arcs.append([])
        return tid

    for bi, b in enumerate(blocks):
        n = len(b)
        adj: list[list[tuple[int, int, int]]] = [[] for _ in range(n)]
        for i in range(n):
            ch = b[i]
            if ch not in whole:
                tid = get_tid(ch)
                aid = len(arc_tid)
                arc_tid.append(tid)
                tok_arcs[tid].append(aid)
                arc_meta.append((bi, i, i + 1, tid))
                adj[i].append((aid, i + 1, tid))
            for tok in by_first.get(ch, ()):
                tlen = len(tok)
                if i + tlen <= n and b.startswith(tok, i):
                    tid = get_tid(tok)
                    aid = len(arc_tid)
                    arc_tid.append(tid)
                    tok_arcs[tid].append(aid)
                    arc_meta.append((bi, i, i + tlen, tid))
                    adj[i].append((aid, i + tlen, tid))
        block_dags.append(adj)

    return blocks, block_dags, id_to_tok, arc_tid, tok_arcs, arc_meta


def verify_integer_lagrangian_cert(
    blocks: list[str],
    block_dags: list[list[list[tuple[int, int, int]]]],
    tok_arcs: list[list[int]],
    lam: list[float],
    scale: int = 1_000_000,
) -> tuple[bool, Fraction]:
    """Convert float multipliers `lam` to exact integer weights and independently verify the exact
    Fraction potential lower bound via exact integer DAG shortest paths (zero floating-point trust).
    """
    int_lam = [max(0, int(round(v * scale))) for v in lam]
    # Compute exact integer max token charge
    max_charge = 0
    for aids in tok_arcs:
        s = sum(int_lam[aid] for aid in aids)
        if s > max_charge:
            max_charge = s
    if max_charge == 0:
        return True, Fraction(0)

    # Exact integer topological DAG shortest path on every block -> exact potentials pi_b[v]
    INF = 10**30
    total_dist = 0
    # Independent check: pi[j] - pi[i] <= int_lam[aid] for every arc, so sum_{a in occ(t)} max(0, pi[j]-pi[i]) <= max_charge!
    tok_pot_charge = [0] * len(tok_arcs)
    for bi, adj in enumerate(block_dags):
        n = len(adj)
        dist = [INF] * (n + 1)
        dist[0] = 0
        for i in range(n):
            di = dist[i]
            if di == INF:
                continue
            for aid, j, _tid in adj[i]:
                cand = di + int_lam[aid]
                if cand < dist[j]:
                    dist[j] = cand
        if dist[n] == INF:
            return False, Fraction(0)
        total_dist += dist[n]
        for i in range(n):
            di = dist[i]
            if di == INF:
                continue
            for aid, j, tid in adj[i]:
                diff = dist[j] - di
                if diff > 0:
                    tok_pot_charge[tid] += diff

    worst_pot = max(tok_pot_charge, default=1)
    if worst_pot == 0:
        return True, Fraction(0)
    # Exact verified rational lower bound = total_dist / worst_pot (since dividing pi by worst_pot guarantees charge <= 1!)
    return True, Fraction(total_dist, worst_pot)


def canzar_lagrangian_decide(
    programs: list[str],
    k: int,
    budget: int,
    max_bytes: int = 160,
    timeout_s: float = 60.0,
    max_iters: int = 400,
) -> dict:
    """Canzar et al. (2012) shortest-path Lagrangian relaxation + primal shortest-path extraction."""
    t0 = time.perf_counter()
    whole = set(programs)
    alpha = sorted(set("".join(programs)))
    all_singletons_ok = all(ch not in whole for ch in alpha)
    if all_singletons_ok and len(alpha) <= budget:
        v = verify_construction(programs, alpha, k, max_bytes=max_bytes)
        return {
            "status": "FEASIBLE",
            "certifiedLowerBound": None,
            "dictionarySize": v["dictionarySize"],
            "phase": "singleton",
            "iterations": 0,
            "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    blocks, block_dags, id_to_tok, arc_tid, tok_arcs, arc_meta = build_block_dags(programs, k=k, max_bytes=max_bytes)
    num_t = len(id_to_tok)
    num_a = len(arc_tid)
    build_ms = (time.perf_counter() - t0) * 1000.0

    # Check unspellable block (empty DAG path)
    if any(len(adj[i]) == 0 for adj in block_dags for i in range(len(adj))):
        pass  # handled naturally by INF shortest path

    # Smart initialization:
    # 1) Single-char forced blocks (len==1) have a single arc -> give that arc weight 1.0 and 0 elsewhere for that token
    # 2) All other tokens: uniform 1 / |occ(t)| across occurrences
    lam = [0.0] * num_a
    pinned_tids: set[int] = set()
    for bi, b in enumerate(blocks):
        if len(b) == 1 and len(block_dags[bi][0]) == 1:
            aid, _, tid = block_dags[bi][0][0]
            lam[aid] = 1.0
            pinned_tids.add(tid)
    for tid, aids in enumerate(tok_arcs):
        if tid in pinned_tids or not aids:
            continue
        w = 1.0 / len(aids)
        for aid in aids:
            lam[aid] = w

    best_lb_float = 0.0
    best_lb_lam = list(lam)
    best_ub = len(alpha) if all_singletons_ok else num_t
    gamma = 2.0
    stall = 0
    INF = 1e30
    iters_done = 0
    active_tids: set[int] = set(pinned_tids)
    tid_freq: dict[int, int] = defaultdict(int)

    for it in range(1, max_iters + 1):
        if time.perf_counter() - t0 >= timeout_s:
            ok, exact_val = verify_integer_lagrangian_cert(blocks, block_dags, tok_arcs, best_lb_lam)
            cert_lb = math.ceil(exact_val) if ok else None
            return {
                "status": "IMPOSSIBLE" if (cert_lb is not None and cert_lb > budget) else "TIMEOUT",
                "certifiedLowerBound": cert_lb,
                "exactPotentialValue": str(exact_val) if ok else None,
                "dictionarySize": None,
                "phase": "lagrangian-timeout",
                "iterations": iters_done,
                "numArcs": num_a,
                "numTokens": num_t,
                "buildMs": round(build_ms, 2),
                "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
            }
        iters_done = it

        # Topological DAG shortest path on every block
        dual_val = 0.0
        used_arcs: list[int] = []
        used_tids: set[int] = set()
        for bi, adj in enumerate(block_dags):
            n = len(adj)
            dist = [INF] * (n + 1)
            par_node = [-1] * (n + 1)
            par_arc = [-1] * (n + 1)
            par_tid = [-1] * (n + 1)
            dist[0] = 0.0
            for i in range(n):
                di = dist[i]
                if di >= INF:
                    continue
                for aid, j, tid in adj[i]:
                    cand = di + lam[aid]
                    if cand < dist[j]:
                        dist[j] = cand
                        par_node[j] = i
                        par_arc[j] = aid
                        par_tid[j] = tid
            if dist[n] >= INF:
                return {
                    "status": "IMPOSSIBLE",
                    "certifiedLowerBound": None,
                    "dictionarySize": None,
                    "phase": "unspellable-dag",
                    "iterations": it,
                    "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                }
            dual_val += dist[n]
            cur = n
            while cur > 0:
                used_arcs.append(par_arc[cur])
                used_tids.add(par_tid[cur])
                cur = par_node[cur]
        for tid in used_tids:
            tid_freq[tid] += 1
        if it <= 40 or it % 5 == 0:
            active_tids |= used_tids

        if dual_val > best_lb_float + 1e-9:
            best_lb_float = dual_val
            best_lb_lam = list(lam)
            stall = 0
            # Early certified IMPOSSIBLE exit once float dual exceeds budget!
            if best_lb_float > budget + 1e-6:
                ok, exact_val = verify_integer_lagrangian_cert(blocks, block_dags, tok_arcs, best_lb_lam)
                if ok and math.ceil(exact_val) > budget:
                    return {
                        "status": "IMPOSSIBLE",
                        "certifiedLowerBound": math.ceil(exact_val),
                        "exactPotentialValue": str(exact_val),
                        "dictionarySize": None,
                        "phase": "lagrangian-shortest-path",
                        "iterations": it,
                        "numArcs": num_a,
                        "numTokens": num_t,
                        "buildMs": round(build_ms, 2),
                        "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                    }
        else:
            stall += 1
            if stall >= 15:
                gamma *= 0.5
                stall = 0
                if gamma < 1e-4:
                    break

        # Primal check from shortest-path token union
        primal_size = len(used_tids)
        if primal_size < best_ub:
            best_ub = primal_size
        if primal_size <= budget:
            cand_dict = [id_to_tok[tid] for tid in used_tids]
            v = verify_construction(programs, cand_dict, k, max_bytes=max_bytes)
            return {
                "status": "FEASIBLE",
                "certifiedLowerBound": math.floor(best_lb_float),
                "dictionarySize": v["dictionarySize"],
                "dictionaryMulti": [t for t in v["dictionary"] if len(t) > 1],
                "phase": "lagrangian-primal-sp",
                "iterations": it,
                "numArcs": num_a,
                "numTokens": num_t,
                "buildMs": round(build_ms, 2),
                "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
            }
        # Light primal greedy prune when within 4 slots of budget
        if primal_size <= budget + 4 and (it <= 5 or it % 10 == 0):
            cand_dict = sorted((id_to_tok[tid] for tid in used_tids), key=lambda t: (-len(t), t))
            for tok in list(cand_dict):
                rest = [d for d in cand_dict if d != tok]
                if all(parse_program(b, rest) is not None for b in blocks):
                    cand_dict = rest
                    if len(cand_dict) <= budget:
                        v = verify_construction(programs, cand_dict, k, max_bytes=max_bytes)
                        return {
                            "status": "FEASIBLE",
                            "certifiedLowerBound": math.floor(best_lb_float),
                            "dictionarySize": v["dictionarySize"],
                            "dictionaryMulti": [t for t in v["dictionary"] if len(t) > 1],
                            "phase": "lagrangian-primal-pruned",
                            "iterations": it,
                            "numArcs": num_a,
                            "numTokens": num_t,
                            "buildMs": round(build_ms, 2),
                            "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                        }

        # Held-Karp / Polyak subgradient step + exact per-token simplex projection!
        # Subgradient g_a = +1 for each arc in used_arcs (0 otherwise).
        # Target UB = min(best_ub, budget + 1.0) when chasing IMPOSSIBLE, or best_ub for general convergence.
        target = max(dual_val + 0.5, float(best_ub))
        norm_sq = float(len(used_arcs))
        if norm_sq <= 0.0:
            break
        step = gamma * (target - dual_val) / norm_sq

        touched_tids: set[int] = set()
        for aid in used_arcs:
            tid = arc_tid[aid]
            if tid in pinned_tids:
                continue
            lam[aid] += step
            touched_tids.add(tid)

        for tid in touched_tids:
            aids = tok_arcs[tid]
            if len(aids) == 1:
                if lam[aids[0]] > 1.0:
                    lam[aids[0]] = 1.0
            else:
                proj = _project_simplex_le_one([lam[aid] for aid in aids])
                for aid, pv in zip(aids, proj):
                    lam[aid] = pv

    # Final exact integer verification of best dual multiplier found
    ok, exact_val = verify_integer_lagrangian_cert(blocks, block_dags, tok_arcs, best_lb_lam)
    cert_lb = math.ceil(exact_val) if ok else None
    if cert_lb is not None and cert_lb > budget:
        return {
            "status": "IMPOSSIBLE",
            "certifiedLowerBound": cert_lb,
            "exactPotentialValue": str(exact_val),
            "dictionarySize": None,
            "phase": "lagrangian-final-cert",
            "iterations": iters_done,
            "numArcs": num_a,
            "numTokens": num_t,
            "buildMs": round(build_ms, 2),
            "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    # Primal active-set MILP over the Lagrangian-selected shortest-path tokens (plus singletons)
    # when dual did not prove IMPOSSIBLE and time remains.
    rem = timeout_s - (time.perf_counter() - t0)
    if rem > 0.25 and active_tids:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import coo_matrix, vstack

        # Keep singletons + top active multi-char tokens by shortest-path frequency
        singleton_tids = {tid for tid, tok in enumerate(id_to_tok) if len(tok) == 1}
        ranked_multi = sorted((tid for tid in active_tids if tid not in singleton_tids), key=lambda t: (-tid_freq[t], t))[:500]
        keep_tids = sorted(singleton_tids | set(ranked_multi))
        tid_remap = {tid: idx for idx, tid in enumerate(keep_tids)}
        sub_arcs = [(bi, i, j, tid_remap[tid]) for bi, i, j, tid in arc_meta if tid in tid_remap]
        num_st = len(keep_tids)
        num_sa = len(sub_arcs)
        offsets: list[int] = []
        nodes = 0
        for b in blocks:
            offsets.append(nodes)
            nodes += len(b) + 1
        r_eq: list[int] = []
        c_eq: list[int] = []
        v_eq: list[float] = []
        b_eq = np.zeros(nodes)
        for bi, b in enumerate(blocks):
            b_eq[offsets[bi]] = 1.0
            b_eq[offsets[bi] + len(b)] = -1.0
        for a_idx, (bi, i, j, _stid) in enumerate(sub_arcs):
            r_eq += [offsets[bi] + i, offsets[bi] + j]
            c_eq += [num_st + a_idx, num_st + a_idx]
            v_eq += [1.0, -1.0]
        A_eq = coo_matrix((v_eq, (r_eq, c_eq)), shape=(nodes, num_st + num_sa)).tocsr()
        r_ub = np.repeat(np.arange(num_sa), 2)
        c_ub = np.empty(2 * num_sa, dtype=np.int32)
        c_ub[0::2] = num_st + np.arange(num_sa)
        c_ub[1::2] = [stid for _, _, _, stid in sub_arcs]
        v_ub = np.tile([1.0, -1.0], num_sa)
        A_ub = coo_matrix((v_ub, (r_ub, c_ub)), shape=(num_sa, num_st + num_sa)).tocsr()
        A_all = vstack([A_eq, A_ub]).tocsr()
        low = np.r_[b_eq, np.full(num_sa, -np.inf)]
        high = np.r_[b_eq, np.zeros(num_sa)]
        cost = np.r_[np.ones(num_st), np.zeros(num_sa)]
        integrality = np.r_[np.ones(num_st), np.zeros(num_sa)]
        milp_res = milp(
            cost,
            constraints=LinearConstraint(A_all, low, high),
            integrality=integrality,
            bounds=Bounds(0, 1),
            options={"time_limit": rem},
        )
        if milp_res.x is not None:
            chosen = [id_to_tok[keep_tids[idx]] for idx in range(num_st) if milp_res.x[idx] > 0.5]
            if len(chosen) <= budget and all(parse_program(b, chosen) is not None for b in blocks):
                v = verify_construction(programs, chosen, k, max_bytes=max_bytes)
                return {
                    "status": "FEASIBLE",
                    "certifiedLowerBound": cert_lb,
                    "exactPotentialValue": str(exact_val) if ok else None,
                    "dictionarySize": v["dictionarySize"],
                    "dictionaryMulti": [t for t in v["dictionary"] if len(t) > 1],
                    "phase": "lagrangian-active-milp",
                    "iterations": iters_done,
                    "activeTokens": num_st,
                    "numArcs": num_a,
                    "numTokens": num_t,
                    "buildMs": round(build_ms, 2),
                    "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                }

    return {
        "status": "UNRESOLVED",
        "certifiedLowerBound": cert_lb,
        "exactPotentialValue": str(exact_val) if ok else None,
        "bestPrimalUB": best_ub,
        "dictionarySize": None,
        "phase": "lagrangian-stalled",
        "iterations": iters_done,
        "numArcs": num_a,
        "numTokens": num_t,
        "buildMs": round(build_ms, 2),
        "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
    }


if __name__ == "__main__":
    import json
    # Dev sanity check on prior C-1/C-2 and B01..B12 (NOT new public repos)
    d = json.loads((HERE.parent / "capacity-race-v1" / "boundary-instances.json").read_text())
    for cid, budget in [("B01", 57), ("B02", 58), ("B03", 62), ("B05", 64), ("B07", 64), ("B07", 66), ("B10", 64), ("B11", 64)]:
        progs = d["corpora"][cid]["programs"]
        r = canzar_lagrangian_decide(progs, 2, budget, timeout_s=15.0)
        print(f"{cid} K={budget}: {r['status']:10s} LB={r.get('certifiedLowerBound')} D={r.get('dictionarySize')} "
              f"it={r.get('iterations')} build={r.get('buildMs')}ms tot={r['elapsedMs']}ms ({r['phase']})")
