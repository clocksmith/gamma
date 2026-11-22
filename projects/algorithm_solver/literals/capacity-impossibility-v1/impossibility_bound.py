#!/usr/bin/env python3
"""Disjoint-Position Cover-Set Impossibility Bound, Scale-1 Dual Shortcut, and 6-Corpus Sweep.

The disjoint-position bound is combinatorial and always sound:
      |F_1(k)| <= B_disj(k) <= OPT_A(k) <= |Sigma|.
When a pairwise-disjoint witness W = F_1(k) cup M(k) reaches |Sigma| it meets the single-character
dictionary, so OPT_A(k) = |Sigma| with no LP or MILP call.

The scale = 1 step potential pi_W is a narrower statement. The Experiment A dual sums over every
occurrence of a token, so a token that overlaps itself across one witness position is charged twice
(in "aaa", "aa" spans position 1 from both of its starts). L_A(pi_W) = B_disj(k) holds exactly when no
eligible token is charged twice. Each receipt row records the dual value and that count.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix

PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
LIT = "projects/algorithm_solver/literals"
THRESHOLDS = (1, 2, 3, 4, 5, 8, 10)
LP_SCALE = 1 << 20


def git_cat(repo: Path, rev_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob", rev_path]
    )


def git_ls(repo: Path, prefix: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), "ls-tree", "-r", "--name-only", PIN, "--", prefix]
    ).decode("utf-8")
    return [line for line in out.splitlines() if line.strip()]


def wit_extents_fast(texts: dict[str, str]) -> dict[tuple[str, int], int]:
    """O(N log N) exact longest substring length starting at (pid, i) shared by >= 2 distinct programs,
    computed via sorted suffixes and adjacent distinct-program LCP."""
    items: list[tuple[str, str, int]] = []
    for pid, s in texts.items():
        for i in range(len(s)):
            items.append((s[i:], pid, i))
    items.sort(key=lambda x: x[0])

    def lcp_len(a: str, b: str) -> int:
        m = min(len(a), len(b))
        idx = 0
        while idx < m and a[idx] == b[idx]:
            idx += 1
        return idx

    m_total = len(items)
    wit: dict[tuple[str, int], int] = {(pid, i): 0 for _suf, pid, i in items}
    # Forward pass: nearest preceding suffix from a different program
    prev_diff_suf: str | None = None
    prev_run_suf: str | None = None
    prev_run_pid: str | None = None
    for suf, pid, i in items:
        if prev_run_pid is not None and prev_run_pid != pid:
            prev_diff_suf = prev_run_suf
        if prev_diff_suf is not None:
            v = lcp_len(suf, prev_diff_suf)
            if v > wit[pid, i]:
                wit[pid, i] = v
        prev_run_suf = suf
        prev_run_pid = pid

    # Backward pass: nearest succeeding suffix from a different program
    next_diff_suf: str | None = None
    next_run_suf: str | None = None
    next_run_pid: str | None = None
    for suf, pid, i in reversed(items):
        if next_run_pid is not None and next_run_pid != pid:
            next_diff_suf = next_run_suf
        if next_diff_suf is not None:
            v = lcp_len(suf, next_diff_suf)
            if v > wit[pid, i]:
                wit[pid, i] = v
        next_run_suf = suf
        next_run_pid = pid

    return wit


def shared_substrings(texts: dict[str, str], max_bytes: int | None = 160):
    """Find all non-whole substrings of length >= 2 (UTF-8 <= max_bytes) occurring in >= 2 distinct programs."""
    whole = set(texts.values())
    alpha = set().union(*map(set, whole)) - whole
    wit = wit_extents_fast(texts)
    docs: dict[str, set[str]] = defaultdict(set)
    occs_raw: list[tuple[str, int, int, str]] = []
    for pid, s in texts.items():
        n = len(s)
        for a in range(n):
            w = wit[pid, a]
            if w < 2:
                continue
            hi = n if max_bytes is None else min(n, a + max_bytes)
            hi = min(hi, a + w)
            b_bytes = len(s[a : a + 1].encode("utf-8"))
            for b in range(a + 2, hi + 1):
                b_bytes += len(s[b - 1 : b].encode("utf-8"))
                if max_bytes is not None and b_bytes > max_bytes:
                    break
                sub = s[a:b]
                if sub not in whole:
                    docs[sub].add(pid)
                    occs_raw.append((pid, a, b, sub))
    doc_freq = {sub: len(d) for sub, d in docs.items() if len(d) >= 2}
    occs = [(pid, a, b, sub) for pid, a, b, sub in occs_raw if sub in doc_freq]
    return whole, alpha, doc_freq, occs, wit


def position_cover_set(
    texts: dict[str, str],
    pid: str,
    pos: int,
    k: int,
    whole: set[str],
    doc_freq: dict[str, int] | None = None,
    max_bytes: int | None = 160,
    wit: dict[tuple[str, int], int] | None = None,
) -> set[str]:
    """Recompute C_k(pid, pos) directly from definitions."""
    s = texts[pid]
    n = len(s)
    assert 0 <= pos < n
    if k == 1:
        if wit is None:
            return {s[a:b] for a in range(pos + 1) for b in range(pos + 1, n + 1) if s[a:b] not in whole}
        shared = set()
        if s[pos] not in whole:
            shared.add(s[pos])
        for a in range(pos + 1):
            w = wit[pid, a]
            if a + w > pos:
                for b in range(pos + 1, a + w + 1):
                    sub = s[a:b]
                    if sub not in whole:
                        shared.add(sub)
        return shared
    assert doc_freq is not None
    out = set()
    if s[pos] not in whole:
        out.add(s[pos])
    lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
    for a in range(lo, pos + 1):
        hi = n if max_bytes is None else min(n, a + max_bytes)
        for b in range(max(pos + 1, a + 2), hi + 1):
            sub = s[a:b]
            if (max_bytes is None or len(sub.encode("utf-8")) <= max_bytes) and sub not in whole:
                if doc_freq.get(sub, 0) >= k:
                    out.add(sub)
    return out


def all_occurrences_dual_fields(texts, k, positions, whole, alpha, doc_freq, occs, wit) -> dict:
    """Value of the Experiment A dual at the scale = 1 step potential of a disjoint witness.

    The dual charges a token once for every (occurrence, witness position) pair where the occurrence spans
    the position. With no token charged twice the value is |W|; each extra charge lowers it by one."""
    from replay_verify_receipt import witness_charges

    positions = [(str(pid), int(pos)) for pid, pos in positions]
    charged = witness_charges(texts, k, positions, whole, alpha, doc_freq, occs, wit)
    penalty = sum(len(where) - 1 for where in charged.values())
    return {
        "all_occurrences_dual": len(positions) - penalty,
        "tokens_counted_twice": len(charged),
        "dual_equals_disjoint_bound": penalty == 0,
    }


def step_potentials_from_witness(
    texts: dict[str, str],
    witness_positions: list[tuple[str, int]],
) -> dict[str, list[int]]:
    """Construct exact scale = 1 integer dual potentials pi_W from disjoint witness positions."""
    by_pid: dict[str, list[int]] = defaultdict(list)
    for pid, pos in witness_positions:
        by_pid[pid].append(pos)
    potentials: dict[str, list[int]] = {}
    for pid, s in texts.items():
        wpos = sorted(by_pid.get(pid, ()))
        potentials[pid] = [sum(1 for wp in wpos if wp >= j) for j in range(len(s) + 1)]
    return potentials


def anchored_u_conflict_sets(
    texts: dict[str, str],
    pid: str,
    pos: int,
    whole: set[str],
    wit: dict[tuple[str, int], int],
) -> tuple[set[str], set[str]]:
    """Minimal shared-witness sets for position (pid, pos) under rule U across distinct programs:
    Two positions (p, i) and (q, j) with p != q have C_U(p, i) cap C_U(q, j) != empty
    iff right(p, i) cap left(q, j) != empty OR left(p, i) cap right(q, j) != empty
    (unless a shorter whole program is a substring inside a shared match, checked separately).
    Takes O(n) strings per position instead of O(n^2)!"""
    s = texts[pid]
    n = len(s)
    w_right = wit[pid, pos]
    right = {s[pos : pos + L] for L in range(1, w_right + 1) if s[pos : pos + L] not in whole}
    left = set()
    for a in range(pos + 1):
        if a + wit[pid, a] > pos:
            sub = s[a : pos + 1]
            if sub not in whole:
                left.add(sub)
    return right, left


def verify_impossibility_witness(
    texts: dict[str, str],
    k: int,
    forced_positions: list[tuple[str, int]],
    extra_positions: list[tuple[str, int]],
    doc_freq: dict[str, int] | None = None,
    max_bytes: int | None = 160,
    wit: dict[tuple[str, int], int] | None = None,
) -> dict:
    """Independently verify a disjoint-position witness W and verify L_A(pi_W) == |W| at scale = 1."""
    whole = set(texts.values())
    if k >= 2 and doc_freq is None:
        _, _, doc_freq, _, _ = shared_substrings(texts, max_bytes=max_bytes)
    if k == 1 and wit is None:
        wit = wit_extents_fast(texts)
        min_whole_len = min(len(x) for x in whole)
    else:
        min_whole_len = min(len(x) for x in whole)

    seen_coords: set[tuple[str, int]] = set()
    seen_pids_u: set[str] = set()
    if k == 1 and min_whole_len > 2:
        # Fast O(|W|^2 * L) exact cross-program disjointness check via anchored right/left sets!
        rl_list: list[tuple[set[str], set[str]]] = []
        for idx, (pid, pos) in enumerate(forced_positions + extra_positions):
            if (pid, pos) in seen_coords:
                raise ValueError(f"Duplicate witness coordinate {(pid, pos)}")
            seen_coords.add((pid, pos))
            s = texts[pid]
            if idx < len(forced_positions):
                full_cset = position_cover_set(texts, pid, pos, 1, whole, wit=None)
                if len(full_cset) != 1:
                    raise ValueError(f"Forced U witness {(pid, pos)} has |C_U|={len(full_cset)} != 1")
                ch_tok = next(iter(full_cset))
                rl_list.append(({ch_tok}, {ch_tok}))
            else:
                if pid in seen_pids_u:
                    raise ValueError(f"Rule U distinct-program witness repeats program {pid}")
                seen_pids_u.add(pid)
                rset, lset = anchored_u_conflict_sets(texts, pid, pos, whole, wit)
                rl_list.append((rset, lset))
        for a_i in range(len(rl_list)):
            r1, l1 = rl_list[a_i]
            for b_i in range(a_i + 1, len(rl_list)):
                r2, l2 = rl_list[b_i]
                if not r1.isdisjoint(l2) or not l1.isdisjoint(r2):
                    raise ValueError("Rule U witness cover sets overlap!")
        total_w = len(rl_list)
    else:
        cover_sets: list[set[str]] = []
        for idx, (pid, pos) in enumerate(forced_positions + extra_positions):
            if (pid, pos) in seen_coords:
                raise ValueError(f"Duplicate witness coordinate {(pid, pos)}")
            seen_coords.add((pid, pos))
            if k == 1:
                s = texts[pid]
                if idx < len(forced_positions):
                    full_cset = position_cover_set(texts, pid, pos, 1, whole, wit=None)
                    if len(full_cset) != 1:
                        raise ValueError(f"Forced U witness {(pid, pos)} has |C_U|={len(full_cset)} != 1")
                    cset = full_cset
                else:
                    if pid in seen_pids_u:
                        raise ValueError(f"Rule U distinct-program witness repeats program {pid}")
                    seen_pids_u.add(pid)
                    cset = position_cover_set(texts, pid, pos, 1, whole, wit=None)
                    if not cset:
                        raise ValueError(f"Empty C_U at {(pid, pos)}")
            else:
                cset = position_cover_set(texts, pid, pos, k, whole, doc_freq=doc_freq, max_bytes=max_bytes)
                if not cset:
                    raise ValueError(f"Empty cover set at {(pid, pos)}")
                if idx < len(forced_positions) and len(cset) != 1:
                    raise ValueError(f"Forced singleton witness {(pid, pos)} has |C_k|={len(cset)} != 1")
            cover_sets.append(cset)
        used: set[str] = set()
        for cset in cover_sets:
            overlap = used & cset
            if overlap:
                raise ValueError(f"Witness cover sets overlap on token(s): {sorted(overlap)[:3]}")
            used |= cset
        total_w = len(cover_sets)

    potentials = step_potentials_from_witness(texts, list(forced_positions) + list(extra_positions))
    telescoping = sum(potentials[pid][0] - potentials[pid][-1] for pid in texts)
    assert telescoping == total_w
    _whole, alpha_all, doc_freq_all, occs_all, wit_all = shared_substrings(texts, max_bytes=max_bytes)
    dual = all_occurrences_dual_fields(
        texts, k, list(forced_positions) + list(extra_positions), whole, alpha_all, doc_freq_all, occs_all, wit_all
    )
    return {
        "valid": True,
        "forced_singletons": len(forced_positions),
        "disjoint_extra": len(extra_positions),
        "disjoint_bound": total_w,
        # The dual sums over occurrences: it equals the disjoint bound only if no token is charged twice.
        "step_potential_dual": dual["all_occurrences_dual"],
        "tokens_counted_twice": dual["tokens_counted_twice"],
        "dual_equals_disjoint_bound": dual["dual_equals_disjoint_bound"],
        "potentials": potentials,
    }


def compute_disjoint_bound_k(
    texts: dict[str, str],
    k: int,
    whole: set[str],
    alpha: set[str],
    doc_freq: dict[str, int],
    occs: list[tuple[str, int, int, str]],
    max_nodes: int = 120_000,
):
    """Fast O(|occs|) difference-array forced-singleton detection + sparse candidate cover sets."""
    assert k >= 2
    # 1. Count multi-char eligible spans covering each position via difference arrays!
    diffs = {pid: [0] * (len(s) + 1) for pid, s in texts.items()}
    for pid, a, b, sub in occs:
        if doc_freq[sub] >= k:
            d = diffs[pid]
            d[a] += 1
            d[b] -= 1

    forced_map: dict[str, tuple[str, int]] = {}
    cands_by_char: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    for pid in sorted(texts.keys()):
        s = texts[pid]
        d = diffs[pid]
        cur = 0
        for i, ch in enumerate(s):
            cur += d[i]
            if ch not in alpha:
                continue
            if cur == 0:
                forced_map.setdefault(ch, (pid, i))
            elif ch not in forced_map:
                cands_by_char[ch].append((cur, pid, i))

    forced_chars = set(forced_map.keys())
    rem_chars = sorted(alpha - forced_chars)
    # Build C_k(pid, pos) ONLY for top-12 lowest-span-count occurrences of each non-forced character,
    # encoded as Python integer bitmasks so DFS conflict checks are O(1) bitwise ops!
    tok_to_bit: dict[str, int] = {}

    def mask_of(tokens: set[str]) -> int:
        m = 0
        for t in tokens:
            b = tok_to_bit.get(t)
            if b is None:
                b = 1 << len(tok_to_bit)
                tok_to_bit[t] = b
            m |= b
        return m

    forced_mask = mask_of(forced_chars)
    cand_per_char: dict[str, list[tuple[int, int, tuple[str, int]]]] = {}
    for ch in rem_chars:
        top_coords = sorted(cands_by_char[ch])[:12]
        seen_masks: dict[int, tuple[int, tuple[str, int]]] = {}
        for _deg, pid, pos in top_coords:
            cset = position_cover_set(texts, pid, pos, k, whole, doc_freq=doc_freq, max_bytes=160)
            msk = mask_of(cset)
            seen_masks.setdefault(msk, (len(cset), (pid, pos)))
        items = sorted(seen_masks.items(), key=lambda kv: kv[1][0])
        minimal: list[tuple[int, int, tuple[str, int]]] = []
        for msk, (sz, coord) in items:
            if not any((prev_msk & ~msk) == 0 for prev_msk, _psz, _pc in minimal):
                minimal.append((msk, sz, coord))
        cand_per_char[ch] = minimal[:10]

    order = sorted(
        rem_chars,
        key=lambda c: (len(cand_per_char[c]), cand_per_char[c][0][1] if cand_per_char[c] else 0),
    )
    best: list[list[tuple[str, int]]] = [[]]
    visited = [0]

    def dfs(idx: int, used_mask: int, chosen: list[tuple[str, int]]):
        visited[0] += 1
        if len(chosen) > len(best[0]):
            best[0] = list(chosen)
        if visited[0] > max_nodes or idx == len(order) or len(chosen) + (len(order) - idx) <= len(best[0]):
            return
        ch = order[idx]
        for msk, _sz, coord in cand_per_char[ch]:
            if (msk & used_mask) == 0:
                chosen.append(coord)
                dfs(idx + 1, used_mask | msk, chosen)
                chosen.pop()
                if len(best[0]) == len(order):
                    return
        dfs(idx + 1, used_mask, chosen)

    dfs(0, forced_mask, [])
    forced_positions = [forced_map[c] for c in sorted(forced_map)]
    extra_positions = best[0]
    checked = verify_impossibility_witness(
        texts, k, forced_positions, extra_positions, doc_freq=doc_freq, max_bytes=160
    )
    return forced_positions, extra_positions, checked["disjoint_bound"]


def compute_disjoint_bound_u(
    texts: dict[str, str],
    wit: dict[tuple[str, int], int] | None = None,
    max_nodes: int = 80_000,
):
    """Find pairwise-disjoint position witness under rule U (k = 1, unrestricted proper substrings)."""
    whole = set(texts.values())
    alpha = set().union(*map(set, whole)) - whole
    if wit is None:
        wit = wit_extents_fast(texts)

    forced_map: dict[str, tuple[str, int]] = {}
    by_char: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    for pid in sorted(texts.keys()):
        s = texts[pid]
        n = len(s)
        diff = [0] * (n + 1)
        for a in range(n):
            w = wit[pid, a]
            if w > 0:
                diff[a] += 1
                diff[a + w] -= 1
        cur = 0
        best_in_prog: dict[str, tuple[int, int]] = {}
        for i, ch in enumerate(s):
            cur += diff[i]
            if ch not in alpha:
                continue
            if n == 1 or (n == 2 and s in whole):
                forced_map.setdefault(ch, (pid, i))
                continue
            prev = best_in_prog.get(ch)
            if prev is None or cur < prev[0]:
                best_in_prog[ch] = (cur, i)
        for ch, (deg, i) in best_in_prog.items():
            if ch not in forced_map:
                by_char[ch].append((deg, pid, i))

    rem_chars = sorted(alpha - set(forced_map))
    filtered = {c: sorted(by_char[c])[:4] for c in rem_chars if by_char[c]}
    order = sorted(filtered.keys(), key=lambda c: (len(filtered[c]), filtered[c][0][0]))
    min_whole_len = min(len(x) for x in whole)
    total_progs = len(texts)

    tok_to_bit: dict[str, int] = {}

    def mask_of(tokens: set[str]) -> int:
        m = 0
        for t in tokens:
            b = tok_to_bit.get(t)
            if b is None:
                b = 1 << len(tok_to_bit)
                tok_to_bit[t] = b
            m |= b
        return m

    pid_to_bit: dict[str, int] = {pid: (1 << idx) for idx, pid in enumerate(sorted(texts.keys()))}
    rl_cache: dict[tuple[str, int], tuple[int, int]] = {}

    def get_rl_mask(pid: str, pos: int) -> tuple[int, int]:
        if (pid, pos) not in rl_cache:
            if min_whole_len > 2:
                rset, lset = anchored_u_conflict_sets(texts, pid, pos, whole, wit)
                rl_cache[pid, pos] = (mask_of(rset), mask_of(lset))
            else:
                full = position_cover_set(texts, pid, pos, 1, whole, wit=None)
                m = mask_of(full)
                rl_cache[pid, pos] = (m, m)
        return rl_cache[pid, pos]

    best: list[list[tuple[str, int]]] = [[]]
    visited = [0]

    def dfs(idx: int, used_pid_mask: int, used_pid_cnt: int, union_r: int, union_l: int, chosen: list[tuple[str, int]]):
        visited[0] += 1
        if len(chosen) > len(best[0]):
            best[0] = list(chosen)
        rem_cap = min(len(order) - idx, total_progs - used_pid_cnt)
        if visited[0] > 40_000 or idx == len(order) or len(chosen) + rem_cap <= len(best[0]):
            return
        ch = order[idx]
        for _deg, pid, pos in filtered[ch]:
            pbit = pid_to_bit[pid]
            if (used_pid_mask & pbit) != 0:
                continue
            rm, lm = get_rl_mask(pid, pos)
            if (rm & union_l) == 0 and (lm & union_r) == 0:
                chosen.append((pid, pos))
                dfs(idx + 1, used_pid_mask | pbit, used_pid_cnt + 1, union_r | rm, union_l | lm, chosen)
                chosen.pop()
                if len(best[0]) == min(len(order), total_progs):
                    return
        dfs(idx + 1, used_pid_mask, used_pid_cnt, union_r, union_l, chosen)

    f_mask = mask_of(set(forced_map.keys()))
    dfs(0, 0, 0, f_mask, f_mask, [])
    forced_positions = [forced_map[c] for c in sorted(forced_map)]
    extra_positions = best[0]
    checked = verify_impossibility_witness(texts, 1, forced_positions, extra_positions, max_bytes=None, wit=wit)
    return forced_positions, extra_positions, checked["disjoint_bound"]


def solve_dual_and_milp_k(
    texts: dict[str, str],
    k: int,
    whole: set[str],
    alpha: set[str],
    doc_freq: dict[str, int],
    occs: list[tuple[str, int, int, str]],
    run_milp: bool = False,
):
    """Compute solver-free integer Lagrangian dual bound ceil(L_A(pi)) via HiGHS LP
    (and optionally MILP feasible upper bound) on small non-saturated instances."""
    progs = sorted(texts.keys(), key=lambda x: (len(x), x))
    strings = sorted(alpha) + sorted(s for s, df in doc_freq.items() if df >= k)
    s_idx = {s: idx for idx, s in enumerate(strings)}
    tails, heads, str_ids = [], [], []
    node_base, sinks, nodes = {}, {}, 0
    occs_by_pid: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for pid, a, b, s in occs:
        if doc_freq[s] >= k:
            occs_by_pid[pid].append((a, b, s))

    for pid in progs:
        t = texts[pid]
        n = len(t)
        base = nodes
        node_base[pid], sinks[pid] = base, base + n
        nodes += n + 1
        for i, ch in enumerate(t):
            if ch in s_idx:
                tails.append(base + i)
                heads.append(base + i + 1)
                str_ids.append(s_idx[ch])
        for a, b, s in occs_by_pid[pid]:
            tails.append(base + a)
            heads.append(base + b)
            str_ids.append(s_idx[s])

    ns, na = len(strings), len(tails)
    nv = ns + na
    cost = np.zeros(nv)
    cost[:ns] = 1.0
    tail_arr = np.array(tails, dtype=int)
    head_arr = np.array(heads, dtype=int)
    str_arr = np.array(str_ids, dtype=int)
    ar = np.arange(na)

    r_flow = np.concatenate([tail_arr, head_arr])
    c_flow = np.concatenate([ns + ar, ns + ar])
    v_flow = np.concatenate([np.ones(na), -np.ones(na)])
    rhs_flow = np.zeros(nodes)
    for pid in progs:
        rhs_flow[node_base[pid]] = 1.0
        rhs_flow[sinks[pid]] = -1.0

    rows = np.concatenate([r_flow, nodes + ar, nodes + ar])
    cols = np.concatenate([c_flow, ns + ar, str_arr])
    vals = np.concatenate([v_flow, np.ones(na), -np.ones(na)])
    A = coo_matrix((vals, (rows, cols)), shape=(nodes + na, nv)).tocsc()

    lp = linprog(
        cost,
        A_ub=A[nodes:, :],
        b_ub=np.zeros(na),
        A_eq=A[:nodes, :],
        b_eq=rhs_flow,
        bounds=(0, 1),
        method="highs",
        options={"time_limit": 8.0},
    )
    if not lp.success or lp.eqlin is None:
        return None, None, None, None
    dual_eq = lp.eqlin.marginals
    potentials = {
        pid: [int(round(dual_eq[node_base[pid] + i] * LP_SCALE)) for i in range(len(texts[pid]) + 1)]
        for pid in progs
    }

    numer = sum(potentials[pid][0] - potentials[pid][-1] for pid in progs)
    rebates: dict[str, int] = defaultdict(int)
    for pid in progs:
        p = potentials[pid]
        t = texts[pid]
        for i, ch in enumerate(t):
            if ch in s_idx and p[i] > p[i + 1]:
                rebates[ch] += p[i] - p[i + 1]
        for a, b, s in occs_by_pid[pid]:
            if p[a] > p[b]:
                rebates[s] += p[a] - p[b]
    numer += sum(min(0, LP_SCALE - reb) for reb in rebates.values())
    cert_bound = -(-numer // LP_SCALE)

    milp_vocab = None
    if run_milp:
        integrality = np.zeros(nv)
        integrality[:ns] = 1
        lb_c = np.concatenate([rhs_flow, np.full(na, -np.inf)])
        ub_c = np.concatenate([rhs_flow, np.zeros(na)])
        res = milp(
            cost,
            integrality=integrality,
            bounds=Bounds(np.zeros(nv), np.ones(nv)),
            constraints=LinearConstraint(A, lb_c, ub_c),
            options={"time_limit": 6.0},
        )
        if res.success and res.x is not None:
            milp_vocab = [strings[i] for i in range(ns) if res.x[i] > 0.5]
    return round(float(lp.fun), 4), int(cert_bound), potentials, milp_vocab


def overlapping_non_tiling_counterexample() -> dict:
    """Explicit counterexample proving position-cover feasibility does NOT imply tiling feasibility:
    T = {'1': 'abcd', '2': 'abce', '3': 'fbcd'} under k = 2 (|Sigma| = 6)."""
    texts = {"1": "abcd", "2": "abce", "3": "fbcd"}
    whole, alpha, doc_freq, occs, _wit = shared_substrings(texts, max_bytes=160)
    f_pos, e_pos, disj_b = compute_disjoint_bound_k(texts, 2, whole, alpha, doc_freq, occs)
    lp_val, cert_dual, _pots, milp_vocab = solve_dual_and_milp_k(
        texts, 2, whole, alpha, doc_freq, occs, run_milp=True
    )
    hitting_candidate = {"abc", "bcd", "e", "f"}
    every_pos_hit = all(
        bool(position_cover_set(texts, pid, i, 2, whole, doc_freq=doc_freq) & hitting_candidate)
        for pid, s in texts.items()
        for i in range(len(s))
    )
    return {
        "texts": texts,
        "alphabet_size": len(alpha),
        "forced_singletons": len(f_pos),
        "disjoint_bound": disj_b,
        "hitting_set_upper_bound": len(hitting_candidate),
        "every_position_covered_by_4_tokens": every_pos_hit,
        "certified_lagrangian_dual": cert_dual,
        "exact_tiling_opt": len(milp_vocab) if milp_vocab is not None else None,
        "lp_relaxation": lp_val,
    }


def load_frozen_corpora(repo: Path) -> dict[str, dict]:
    """Load six frozen corpora (JavaScript, Python, and C) pinned at clocksmith/gamma@59ff0441."""
    corpora: dict[str, dict] = {}
    ids80 = json.loads(git_cat(repo, f"{PIN}:{LIT}/matched80-v1/labels/ids.json"))
    js_compact = {
        str(pid): git_cat(repo, f"{PIN}:{LIT}/scale-v2/generated/sources/{pid:04d}-compact.js").decode("utf-8")
        for pid in ids80
    }
    js_canonical = {
        str(pid): git_cat(repo, f"{PIN}:{LIT}/scale-v2/generated/sources/{pid:04d}-canonical.js").decode("utf-8")
        for pid in ids80
    }
    # Load pinned A-U compact certificate (79) and feasible vocabulary (79) from 59ff0441
    au_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/sixbit-v1/run-v1/a-u-compact/manifest.json"))
    au_cert = json.loads(git_cat(repo, f"{PIN}:{LIT}/sixbit-v1/run-v1/a-u-compact/certificate.json"))
    # Load pinned A-U canonical feasible vocabulary (79) from supplement if present
    try:
        auc_manifest = json.loads(
            git_cat(repo, f"{PIN}:{LIT}/sixbit-v1/run-jupiter-v1/a-u-canonical/manifest.json")
        )
        auc_vocab = auc_manifest["vocabulary"]
    except Exception:
        auc_vocab = None

    corpora["js_matched80_compact"] = {
        "language": "JavaScript (matched80 compact)",
        "texts": js_compact,
        "pinned_u_cert": au_cert,
        "pinned_u_vocab": au_manifest["vocabulary"],
    }
    corpora["js_matched80_canonical"] = {
        "language": "JavaScript (matched80 canonical)",
        "texts": js_canonical,
        "pinned_u_cert": None,
        "pinned_u_vocab": auc_vocab,
    }

    sub12_ids = [str(pid) for pid in sorted(ids80)[:12]]
    corpora["js_sub12_compact"] = {
        "language": "JavaScript (12-program sub-cohort)",
        "texts": {pid: js_compact[pid] for pid in sub12_ids},
        "pinned_u_cert": None,
        "pinned_u_vocab": None,
    }

    # Frozen Python corpus 1: paired-authoring-v1 first 80 Python programs (pinned in 59ff0441)
    pa_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/paired-authoring-v1/manifest.json"))
    py_rows80 = sorted(
        [r for r in pa_manifest["source_inventory"] if r["language"] == "python"],
        key=lambda r: int(r["problem_id"]),
    )[:80]
    py_paired80 = {}
    for row in py_rows80:
        pid = str(row["problem_id"])
        raw = git_cat(repo, f"{PIN}:{LIT}/paired-authoring-v1/{row['path']}")
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        py_paired80[pid] = raw.decode("utf-8")

    # Frozen Python corpus 2: python-devval-v1 100 Python programs (pinned in 59ff0441)
    dv_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/python-devval-v1/manifest.json"))
    py_readable = {}
    for row in dv_manifest["sources"]:
        pid = str(row.get("problem_id") or row.get("id"))
        raw = git_cat(repo, f"{PIN}:{LIT}/python-devval-v1/{row['path']}")
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        py_readable[pid] = raw.decode("utf-8")

    corpora["py_paired80_fit"] = {
        "language": "Python (paired80 dev-fit)",
        "texts": py_paired80,
        "pinned_u_cert": None,
        "pinned_u_vocab": None,
    }
    corpora["py_devval100_readable"] = {
        "language": "Python (devval100 validation)",
        "texts": py_readable,
        "pinned_u_cert": None,
        "pinned_u_vocab": None,
    }

    # Frozen C corpus: all standalone C tools in projects/enwiki9/tools/*.c (64..8192 bytes) at 59ff0441
    c_paths = sorted(p for p in git_ls(repo, "projects/enwiki9/tools") if p.endswith(".c"))
    c_texts = {}
    c_selected_paths = []
    for p in c_paths:
        raw = git_cat(repo, f"{PIN}:{p}")
        if 64 <= len(raw) <= 8192:
            c_selected_paths.append(p)
            c_texts[str(len(c_selected_paths))] = raw.decode("utf-8")
    corpora[f"c_tools_{len(c_texts)}"] = {
        "language": f"C ({len(c_texts)} pinned tools <=8KB)",
        "texts": c_texts,
        "c_paths": c_selected_paths,
        "pinned_u_cert": None,
        "pinned_u_vocab": None,
    }
    return corpora


def evaluate_all(repo: Path, cert_bundle_out: Path | None = None) -> dict:
    t0 = time.time()
    ce = overlapping_non_tiling_counterexample()
    corpora = load_frozen_corpora(repo)
    summary = {}
    cert_bundle: dict[str, dict] = {}

    for cname, meta in corpora.items():
        ct0 = time.time()
        texts = meta["texts"]
        whole, alpha, doc_freq, occs, wit = shared_substrings(texts, max_bytes=160)
        sigma = len(alpha)
        alpha_vocab = sorted(alpha)
        rows = []
        cert_bundle[cname] = {}

        for k in THRESHOLDS:
            if k == 1:
                f_pos, e_pos, disj_b = compute_disjoint_bound_u(texts, wit=wit)
                shortcut = disj_b == sigma
                if shortcut:
                    cert_lb = sigma
                    feas_ub = sigma
                    cert_record = {
                        "type": "disjoint_step_potential_scale1",
                        "scale": 1,
                        "forced_positions": f_pos,
                        "extra_positions": e_pos,
                        "feasible_vocabulary": alpha_vocab,
                    }
                elif meta["pinned_u_cert"] is not None and meta["pinned_u_vocab"] is not None:
                    cert_lb = 79
                    feas_ub = len(meta["pinned_u_vocab"])
                    cert_record = {
                        "type": "pinned_59ff0441_dual_plus_disjoint_witness",
                        "disjoint_forced_positions": f_pos,
                        "disjoint_extra_positions": e_pos,
                        "disjoint_bound": disj_b,
                        "pinned_cert_path": f"{LIT}/sixbit-v1/run-v1/a-u-compact/certificate.json",
                        "pinned_manifest_path": f"{LIT}/sixbit-v1/run-v1/a-u-compact/manifest.json",
                    }
                else:
                    cert_lb = disj_b
                    feas_ub = len(meta["pinned_u_vocab"]) if meta["pinned_u_vocab"] is not None else sigma
                    cert_record = {
                        "type": "disjoint_step_potential_scale1",
                        "scale": 1,
                        "forced_positions": f_pos,
                        "extra_positions": e_pos,
                        "feasible_vocabulary": meta["pinned_u_vocab"] if meta["pinned_u_vocab"] is not None else alpha_vocab,
                    }
                rows.append({
                    "k": 1,
                    "rule": "U (k=1)",
                    "alphabet_size": sigma,
                    "forced_singletons": len(f_pos),
                    "disjoint_bound": disj_b,
                    "certified_lower_bound": cert_lb,
                    "feasible_upper_bound": feas_ub,
                    "remaining_gap": feas_ub - cert_lb,
                    "shortcut_applied": shortcut,
                    "impossible_at_64": cert_lb > 64,
                    **all_occurrences_dual_fields(texts, 1, f_pos + e_pos, whole, alpha, doc_freq, occs, wit),
                })
                cert_bundle[cname]["1"] = cert_record
                continue

            f_pos, e_pos, disj_b = compute_disjoint_bound_k(texts, k, whole, alpha, doc_freq, occs)
            shortcut = disj_b == sigma
            if shortcut:
                cert_lb = sigma
                feas_ub = sigma
                cert_record = {
                    "type": "shortcut_disjoint_scale1",
                    "scale": 1,
                    "forced_positions": f_pos,
                    "extra_positions": e_pos,
                    "feasible_vocabulary": alpha_vocab,
                }
            elif len(occs) <= 25_000 and len(texts) <= 30:
                _lp, lp_cert, lp_pots, milp_vocab = solve_dual_and_milp_k(
                    texts, k, whole, alpha, doc_freq, occs, run_milp=True
                )
                if lp_cert is not None and lp_cert > disj_b and lp_pots is not None:
                    cert_lb = lp_cert
                    feas_vocab = milp_vocab if (milp_vocab is not None and len(milp_vocab) < sigma) else alpha_vocab
                    feas_ub = len(feas_vocab)
                    cert_record = {
                        "type": "lp_dual_certificate_plus_disjoint",
                        "scale": LP_SCALE,
                        "disjoint_forced_positions": f_pos,
                        "disjoint_extra_positions": e_pos,
                        "disjoint_bound": disj_b,
                        "potentials": lp_pots,
                        "certified_lower_bound": cert_lb,
                        "feasible_vocabulary": feas_vocab,
                    }
                else:
                    cert_lb = disj_b
                    feas_vocab = milp_vocab if (milp_vocab is not None and len(milp_vocab) < sigma) else alpha_vocab
                    feas_ub = len(feas_vocab)
                    cert_record = {
                        "type": "disjoint_step_potential_scale1",
                        "scale": 1,
                        "forced_positions": f_pos,
                        "extra_positions": e_pos,
                        "feasible_vocabulary": feas_vocab,
                    }
            else:
                cert_lb = disj_b
                feas_ub = sigma
                cert_record = {
                    "type": "disjoint_step_potential_scale1",
                    "scale": 1,
                    "forced_positions": f_pos,
                    "extra_positions": e_pos,
                    "feasible_vocabulary": alpha_vocab,
                }

            rows.append({
                "k": k,
                "rule": f"W (k={k})",
                "alphabet_size": sigma,
                "forced_singletons": len(f_pos),
                "disjoint_bound": disj_b,
                "certified_lower_bound": cert_lb,
                "feasible_upper_bound": feas_ub,
                "remaining_gap": feas_ub - cert_lb,
                "shortcut_applied": shortcut,
                "impossible_at_64": cert_lb > 64,
                **all_occurrences_dual_fields(texts, k, f_pos + e_pos, whole, alpha, doc_freq, occs, wit),
            })
            cert_bundle[cname][str(k)] = cert_record

        summary[cname] = {
            "language": meta["language"],
            "programs": len(texts),
            "total_utf8_bytes": sum(len(s.encode("utf-8")) for s in texts.values()),
            "alphabet_size": sigma,
            "shared_substrings_k2": len(doc_freq),
            "c_paths": meta.get("c_paths"),
            "transform_sha256": meta.get("transform_sha256"),
            "elapsed_sec": round(time.time() - ct0, 2),
            "rows": rows,
        }

    if cert_bundle_out is not None:
        cert_bundle_out.write_text(json.dumps({"pin": PIN, "certificates": cert_bundle}, indent=2) + "\n", encoding="utf-8")

    return {
        "schema": "gamma.bits.capacity-impossibility-six-corpus-receipt/v1",
        "pin": PIN,
        "thresholds": list(THRESHOLDS),
        "total_elapsed_sec": round(time.time() - t0, 2),
        "non_tiling_counterexample": ce,
        "corpora": summary,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--certs-out", type=Path, default=None)
    args = parser.parse_args()
    res = evaluate_all(args.repo, cert_bundle_out=args.certs_out)
    if args.out is not None:
        args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
