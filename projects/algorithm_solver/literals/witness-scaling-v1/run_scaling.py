#!/usr/bin/env python3
"""Run the pre-registered witness-rule scaling experiment (40 / 80 / 160 cohorts, two source families).

Computes, for every cohort in cohorts.json and every budget K in 0..|Sigma|:
  - single_char[K]: exact single-character coverage (HiGHS MILP on |Sigma|+N vars + replayed set).
  - lower[K]: best verified, replayed W-legal dictionary (single chars, 4-start greedy shortest-path
    witnessed DP with 160-byte cap, and rare-character / tail fragment compression).
  - upper[K]: minimum of 100% solver-free proven ceilings, verified in two prime fields:
      (1) K in {0, 1} -> 0 (every program has length >= 150 and >= 2 distinct bytes);
      (2) whole-program rank nullity bound: K + (N - rank_whole);
      (3) per-program forced-block rank filter (prank[p] <= K) + forced-unit-vector (F_span) exact
          integer-certified LP dual bound (checked solver-free from stored integer duals);
      (4) tail subset block-rank bounds (r_N and r_{N-1} for all cohorts; r_{N-2} for N <= 80).
  - fspan_milp_diagnostic[K]: MILP optimum of F_span (recorded strictly as a non-certificate
    diagnostic, NEVER used in upper[K]).

Also evaluates out-of-sample curve generalization (2-parameter logistic vs. flexible monotone
empirical curve vs. character-only baseline) trained strictly on -a cohorts and scored on held-out
-b cohorts (same-size, cross-size, cross-family), plus the P-80-clustered vs. P-80-diverse contrast.

    python3 -B run_scaling.py [cohorts.json] [results.json]
"""
import collections
import hashlib
import json
import math
import os
import random
import sys
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp, minimize
from scipy.sparse import coo_matrix, lil_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES_W = 160
PRIMES = ((1_000_000_007, 2), (998_244_353, 3))
DUAL_SCALE = 1_000_000


# --------------------------------------------------------------------------- witness rule & replay
def compute_shared_len(sources):
    """For each program p and byte index i, longest length <= MAX_BYTES_W occurring in >= 2 programs."""
    ids = sorted(sources)
    shared_len = {p: [0] * len(sources[p]) for p in ids}
    alive = [(p, i) for p in ids for i in range(len(sources[p]))]
    for length in range(1, MAX_BYTES_W + 1):
        first_owner = {}
        multi = set()
        live = [(p, i) for p, i in alive if i + length <= len(sources[p])]
        for p, i in live:
            sub = sources[p][i:i + length]
            prev = first_owner.get(sub)
            if prev is None:
                first_owner[sub] = p
            elif prev != p:
                multi.add(sub)
        if not multi:
            break
        next_alive = []
        for p, i in live:
            if sources[p][i:i + length] in multi:
                shared_len[p][i] = length
                next_alive.append((p, i))
        alive = next_alive
    return shared_len


def is_legal(words, whole_list, whole_set):
    for w in words:
        if not w or w in whole_set:
            return False
        if len(w) > 1:
            if len(w) > MAX_BYTES_W:
                return False
            c = 0
            for s in whole_list:
                if w in s:
                    c += 1
                    if c >= 2:
                        break
            if c < 2:
                return False
    return True


def replay_spelled(words, ids, sources):
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    out = []
    for p in ids:
        s = sources[p]
        n = len(s)
        reach = [False] * (n + 1)
        reach[0] = True
        for i in range(n):
            if reach[i]:
                for w in by_first.get(s[i], ()):
                    if s.startswith(w, i):
                        reach[i + len(w)] = True
        if reach[n]:
            out.append(p)
    return out


# --------------------------------------------------------------------------- finite-field linear algebra
def rref_matrix(rows, mod):
    if len(rows) == 0:
        return np.zeros((0, 0), dtype=np.int64)
    m = np.array(rows, dtype=np.int64) % mod
    if m.ndim == 1:
        m = m[None, :]
    r = 0
    nrows, ncols = m.shape
    for c in range(ncols):
        nz = np.nonzero(m[r:, c])[0]
        if len(nz) == 0:
            continue
        piv = r + int(nz[0])
        if piv != r:
            m[[r, piv]] = m[[piv, r]]
        inv = pow(int(m[r, c]), mod - 2, mod)
        if inv != 1:
            m[r] = (m[r] * inv) % mod
        fac = m[:, c].copy()
        fac[r] = 0
        nz_rows = np.nonzero(fac)[0]
        if len(nz_rows):
            m[nz_rows] = (m[nz_rows] - fac[nz_rows, None] * m[r][None, :]) % mod
        r += 1
        if r == nrows:
            break
    return m[:r]


def poly_vector(word, col_of, width, mod, base):
    v = [0] * width
    wt = 1
    for ch in word:
        idx = col_of[ch]
        v[idx] = (v[idx] + wt) % mod
        wt = (wt * base) % mod
    return v


def compute_forced_blocks(ids, sources):
    owners = collections.defaultdict(set)
    for idx, p in enumerate(ids):
        s = sources[p]
        for i in range(len(s) - 1):
            owners[s[i:i + 2]].add(idx)
    blocks_by_prog = {}
    for p in ids:
        s = sources[p]
        bs, start = [], 0
        for i in range(len(s) - 1):
            if len(owners[s[i:i + 2]]) < 2:
                bs.append(s[start:i + 1])
                start = i + 1
        bs.append(s[start:])
        blocks_by_prog[p] = bs
    return blocks_by_prog


def algebra_bounds_one_prime(ids, sources, alphabet, blocks_by_prog, mod, base, compute_n_minus_2):
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    whole_rank = len(rref_matrix([poly_vector(sources[p], col_of, width, mod, base) for p in ids], mod))
    nullity = len(ids) - whole_rank

    basis = {}
    prank = {}
    fspan = {}
    for p in ids:
        uniq = sorted(set(blocks_by_prog[p]))
        mat = rref_matrix([poly_vector(b, col_of, width, mod, base) for b in uniq], mod)
        basis[p] = mat
        prank[p] = int(mat.shape[0])
        units = set()
        for row in mat:
            nz = np.nonzero(row)[0]
            if len(nz) == 1:
                units.add(alphabet[int(nz[0])])
        fspan[p] = units

    def stack_rank(mats):
        nonempty = [m for m in mats if m.shape[0] > 0]
        if not nonempty:
            return 0
        return int(rref_matrix(np.vstack(nonempty), mod).shape[0])

    # Prefix / suffix reduced bases for fast N-1 and N-2 rank queries
    n = len(ids)
    r_full = stack_rank([basis[p] for p in ids])

    pref = [np.zeros((0, width), dtype=np.int64)] * (n + 1)
    for i in range(n):
        pref[i + 1] = rref_matrix(np.vstack([pref[i], basis[ids[i]]]), mod) if pref[i].shape[0] else basis[ids[i]]
    suff = [np.zeros((0, width), dtype=np.int64)] * (n + 1)
    for i in range(n - 1, -1, -1):
        suff[i] = rref_matrix(np.vstack([basis[ids[i]], suff[i + 1]]), mod) if suff[i + 1].shape[0] else basis[ids[i]]

    r_n_minus_1 = width
    for i in range(n):
        rk = stack_rank([pref[i], suff[i + 1]])
        if rk < r_n_minus_1:
            r_n_minus_1 = rk

    r_n_minus_2 = None
    if compute_n_minus_2:
        r_n_minus_2 = width
        for i in range(n):
            # Prefix excluding i for indices > i
            cur_pref = pref[i]
            # Suffix excluding nothing for indices > i is already suff[j+1]!
            # So for every j > i, missing {i, j} = cur_pref (0..j-1 excl i) U suff[j+1] (j+1..n-1)!
            for j in range(i + 1, n):
                if cur_pref.shape[0] == width or suff[j + 1].shape[0] == width:
                    rk = width
                else:
                    rk = stack_rank([cur_pref, suff[j + 1]])
                if rk < r_n_minus_2:
                    r_n_minus_2 = rk
                if cur_pref.shape[0] < width:
                    cur_pref = rref_matrix(np.vstack([cur_pref, basis[ids[j]]]), mod) if cur_pref.shape[0] else basis[ids[j]]

    return {
        'wholeRank': whole_rank,
        'wholeNullity': nullity,
        'prank': prank,
        'fspan': fspan,
        'rankFull': r_full,
        'rankNMinus1': r_n_minus_1,
        'rankNMinus2': r_n_minus_2,
    }


# --------------------------------------------------------------------------- exact single-char & F_span LP dual
def solve_char_cover_milp(ids, sets_by_id, alphabet):
    width = len(alphabet)
    col = {c: len(ids) + j for j, c in enumerate(alphabet)}
    nv = len(ids) + width
    pairs = [(i, col[c]) for i, p in enumerate(ids) for c in sets_by_id[p]]
    A = lil_matrix((len(pairs) + 1, nv))
    for r, (i, j) in enumerate(pairs):
        A[r, i] = 1.0
        A[r, j] = -1.0
    A[len(pairs), len(ids):] = 1.0
    A = A.tocsr()
    cost = np.zeros(nv)
    cost[:len(ids)] = -1.0
    out = {}
    for k in range(width + 1):
        ub = np.zeros(len(pairs) + 1)
        ub[-1] = k
        res = milp(cost, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(nv), bounds=Bounds(0, 1))
        assert res.status == 0, f'MILP failed at K={k}: {res.message}'
        chosen = sorted(c for c in alphabet if res.x[col[c]] > 0.5)
        out[k] = (int(round(-res.fun)), chosen)
    return out


def solve_fspan_lp_dual(elig_ids, fspan_by_id, alphabet, budget):
    """Solve LP relaxation of max cover on (elig_ids, fspan) and return exact integer dual certificate."""
    n_p = len(elig_ids)
    if n_p == 0:
        return 0, {'scale': DUAL_SCALE, 'mu': 0, 'alpha': []}
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    c = np.zeros(width + n_p)
    c[width:] = -1.0
    rows, cols, vals = [], [], []
    ri = 0
    edge_meta = []
    for pi, p in enumerate(elig_ids):
        for ch in sorted(fspan_by_id[p]):
            rows.append(ri); cols.append(width + pi); vals.append(1.0)
            rows.append(ri); cols.append(col_of[ch]); vals.append(-1.0)
            edge_meta.append((p, ch, pi))
            ri += 1
    for ci in range(width):
        rows.append(ri); cols.append(ci); vals.append(1.0)
    ub = np.zeros(ri + 1)
    ub[ri] = budget
    A = coo_matrix((vals, (rows, cols)), shape=(ri + 1, width + n_p)).tocsr()
    res = linprog(c, A_ub=A, b_ub=ub, bounds=(0, 1), method='highs')
    assert res.status == 0, f'LP failed at K={budget}: {res.message}'

    duals = -res.ineqlin.marginals
    mu = max(0, int(round(duals[-1] * DUAL_SCALE)))
    alpha_entries = []
    char_load = collections.Counter()
    prog_load = collections.Counter()
    for idx, (p, ch, pi) in enumerate(edge_meta):
        val = max(0, int(round(duals[idx] * DUAL_SCALE)))
        if val > 0:
            alpha_entries.append([p, ch, val])
            char_load[ch] += val
            prog_load[pi] += val
    gamma_sum = sum(max(0, char_load[ch] - mu) for ch in char_load)
    beta_sum = sum(max(0, DUAL_SCALE - prog_load[pi]) for pi in range(n_p))
    cert_ub = (beta_sum + gamma_sum + mu * budget) // DUAL_SCALE
    return int(cert_ub), {'scale': DUAL_SCALE, 'mu': mu, 'alpha': alpha_entries}


# --------------------------------------------------------------------------- lower-end builders
def parse_cost_dp(s, shared_l, by_first, have, bias_single, bias_multi, whole_set):
    n = len(s)
    inf = float('inf')
    f = [inf] * (n + 1)
    back = [0] * (n + 1)
    f[0] = 0.0
    for i in range(n):
        fi = f[i]
        if fi == inf:
            continue
        for w in by_first.get(s[i], ()):
            if s.startswith(w, i) and fi < f[i + len(w)]:
                f[i + len(w)] = fi
                back[i + len(w)] = i
        c1 = fi + 1.0 + bias_single
        if c1 < f[i + 1]:
            f[i + 1] = c1
            back[i + 1] = i
        max_l = min(shared_l[i], MAX_BYTES_W, n - i)
        if max_l >= 2:
            cm = fi + 1.0 + bias_multi
            for j in range(i + 2, i + max_l + 1):
                if cm < f[j]:
                    if j - i == n and s in whole_set:
                        continue
                    f[j] = cm
                    back[j] = i
    pieces = []
    j = n
    while j > 0:
        pieces.append(s[back[j]:j])
        j = back[j]
    return {w for w in pieces if w not in have}


def compress_rare_char_clusters(subset_ids, ids, sources, shared_len, whole_list, whole_set):
    """Try replacing groups of >= 2 characters unique to one shared substring in subset_ids with that substring."""
    sub_sources = {p: sources[p] for p in subset_ids}
    chars = sorted(set(b''.join(sub_sources.values())))
    # Count how many programs in subset_ids use each character, and track every position
    char_occ = collections.defaultdict(list)
    for p in subset_ids:
        s = sources[p]
        for i, ch in enumerate(s):
            char_occ[ch].append((p, i))
    # Candidate rare characters: occur in <= 12 positions across the subset
    rare = [ch for ch in chars if len(char_occ[ch]) <= 12]
    if len(rare) < 2:
        return None
    # Collect candidate shared substrings covering >= 2 distinct rare characters
    cand_subs = collections.Counter()
    rare_set = set(rare)
    for p in subset_ids:
        s = sources[p]
        sl = shared_len[p]
        n = len(s)
        for i in range(n):
            ml = min(sl[i], MAX_BYTES_W, n - i)
            if ml < 2:
                continue
            # Check if s[i:i+ml] contains >= 2 rare chars
            seg = s[i:i + ml]
            if len(rare_set.intersection(seg)) >= 2:
                # Trim to minimal span covering those rare chars
                idxs = [k for k, ch in enumerate(seg) if ch in rare_set]
                sub = seg[idxs[0]:idxs[-1] + 1]
                if 2 <= len(sub) <= MAX_BYTES_W and sub not in whole_set:
                    cand_subs[sub] += 1
    if not cand_subs:
        return None
    # Greedily replace covered rare chars if every occurrence of those chars in subset_ids is covered by sub
    current_chars = set(chars)
    added_frags = set()
    for sub, _ in cand_subs.most_common(64):
        sub_chars = set(sub) & current_chars
        if len(sub_chars) < 2:
            continue
        # Test replacing the subset of chars whose EVERY occurrence in subset_ids can be parsed using (current_chars \ drop) U added_frags U {sub}
        droppable = set()
        for ch in sub_chars:
            # Quick necessary check: every occurrence of ch in subset_ids must lie inside an occurrence of sub
            ok = True
            for p, pos in char_occ[ch]:
                s = sources[p]
                found = False
                start = max(0, pos - len(sub) + 1)
                end = min(len(s) - len(sub), pos)
                for st in range(start, end + 1):
                    if s.startswith(sub, st):
                        found = True
                        break
                if not found:
                    ok = False
                    break
            if ok:
                droppable.add(ch)
        if len(droppable) >= 2:
            trial = {bytes([c]) for c in (current_chars - droppable)} | added_frags | {sub}
            if is_legal(trial, whole_list, whole_set):
                got = set(replay_spelled(trial, subset_ids, sources))
                if len(got) == len(subset_ids):
                    current_chars -= droppable
                    added_frags.add(sub)
    if not added_frags:
        return None
    return {bytes([c]) for c in current_chars} | added_frags


def evaluate_cohort(cohort):
    t0 = time.monotonic()
    cid = cohort['cohortId']
    ids = [p['id'] for p in cohort['programs']]
    sources = {p['id']: p['text'].encode('ascii') for p in cohort['programs']}
    whole_list = [sources[p] for p in ids]
    whole_set = set(whole_list)
    alphabet = sorted(set(b''.join(whole_list)))
    width = len(alphabet)
    n = len(ids)

    # Sanity checks on trivial K=1 bound
    assert all(len(s) >= 2 and len(set(s)) >= 2 for s in whole_list)

    # 1. Single-character exact curve (HiGHS MILP + replay verification)
    need_chars = {p: frozenset(sources[p]) for p in ids}
    singles_milp = solve_char_cover_milp(ids, need_chars, alphabet)

    best = {}  # budget -> (count, source_label, frozenset[bytes])

    def offer(words, label):
        wset = frozenset(words)
        if not wset or len(wset) > width:
            return
        if not is_legal(wset, whole_list, whole_set):
            return
        sp = replay_spelled(wset, ids, sources)
        k = len(wset)
        cnt = len(sp)
        if cnt > best.get(k, (-1,))[0]:
            best[k] = (cnt, label, wset, sp)

    single_sets = {}
    for k in range(width + 1):
        opt, chosen = singles_milp[k]
        words = frozenset(bytes([c]) for c in chosen)
        sp = replay_spelled(words, ids, sources) if words else []
        assert len(sp) == opt, f'{cid} K={k}: single replay {len(sp)} != {opt}'
        single_sets[str(k)] = {'characters': bytes(chosen).decode('ascii'), 'spells': opt}
        if words:
            offer(words, 'single characters')

    # 2. Shared fragment lengths + 4-start greedy witnessed DP
    shared_len = compute_shared_len(sources)

    def run_greedy(bias_single, bias_multi, seed, label):
        rng = random.Random(seed) if seed is not None else None
        have = set()
        group = set()
        by_first = collections.defaultdict(list)
        while len(group) < n and len(have) < width:
            options = []
            for p in ids:
                if p in group:
                    continue
                new = parse_cost_dp(sources[p], shared_len[p], by_first, have, bias_single, bias_multi, whole_set)
                tie = rng.random() if rng else 0.0
                options.append((len(new), tie, p, new))
            _, _, p, new = min(options)
            if any(w in whole_set for w in new):
                new = {w for w in new if w not in whole_set} | {bytes([c]) for w in new if w in whole_set for c in w}
            for w in new:
                have.add(w)
                by_first[w[0]].append(w)
            group.add(p)
            if len(have) <= width:
                offer(have, label)

    run_greedy(0.0, 0.001, None, 'greedy DP, single characters preferred')
    run_greedy(0.001, 0.0, None, 'greedy DP, shared fragments preferred')
    run_greedy(0.0, 0.0, f'{cid}/seed0', 'greedy DP, random ties 0')
    run_greedy(0.001, 0.0, f'{cid}/seed1', 'greedy DP, shared fragments preferred, random ties 1')

    # 3. Rare-character fragment compression near top budgets (single-char subsets + full - 0/1/2)
    tested_subsets = set()
    # Full cohort
    comp = compress_rare_char_clusters(ids, ids, sources, shared_len, whole_list, whole_set)
    if comp is not None:
        offer(comp, 'rare-character fragment compression (full)')
    # Best single-char subsets for top 25 budgets
    for k in range(max(1, width - 25), width + 1):
        chosen = frozenset(single_sets[str(k)]['characters'].encode('ascii'))
        sub_ids = tuple(p for p in ids if need_chars[p] <= chosen)
        if sub_ids and sub_ids not in tested_subsets:
            tested_subsets.add(sub_ids)
            comp = compress_rare_char_clusters(list(sub_ids), ids, sources, shared_len, whole_list, whole_set)
            if comp is not None:
                offer(comp, 'rare-character fragment compression')
        # Also try adding 1 uncovered program with fewest missing characters
        uncov = [p for p in ids if not (need_chars[p] <= chosen)]
        if uncov:
            uncov.sort(key=lambda p: (len(need_chars[p] - chosen), p))
            for extra in uncov[:2]:
                sub_plus = tuple(sorted(set(sub_ids) | {extra}))
                if sub_plus not in tested_subsets:
                    tested_subsets.add(sub_plus)
                    comp = compress_rare_char_clusters(list(sub_plus), ids, sources, shared_len, whole_list, whole_set)
                    if comp is not None:
                        offer(comp, 'rare-character fragment compression (+1)')

    # 4. Solver-free algebraic upper bounds in TWO prime fields
    blocks_by_prog = compute_forced_blocks(ids, sources)
    alg = {}
    for mod, base in PRIMES:
        alg[f'{mod}:{base}'] = algebra_bounds_one_prime(
            ids, sources, alphabet, blocks_by_prog, mod, base, compute_n_minus_2=(n <= 80)
        )
    # Take the mathematically sound (most conservative / verified-agreeing) intersection across primes:
    # Actually EVERY single prime field gives a valid lower bound on rank (a true rank over Q or linear
    # dependence over F_p); taking max over valid primes is sound, and we also record whether primes agree!
    p1_key = f'{PRIMES[0][0]}:{PRIMES[0][1]}'
    p2_key = f'{PRIMES[1][0]}:{PRIMES[1][1]}'
    a1, a2 = alg[p1_key], alg[p2_key]
    primes_agree = (
        a1['wholeRank'] == a2['wholeRank']
        and a1['rankFull'] == a2['rankFull']
        and a1['rankNMinus1'] == a2['rankNMinus1']
        and a1['rankNMinus2'] == a2['rankNMinus2']
        and a1['prank'] == a2['prank']
        and a1['fspan'] == a2['fspan']
    )
    # Use prime 1 (1e9+7, base 2) for certified F_span LP duals; checker verifies prime 1 AND prime 2!
    whole_nullity = a1['wholeNullity']
    prank = a1['prank']
    fspan = a1['fspan']
    r_full = a1['rankFull']
    r_nm1 = a1['rankNMinus1']
    r_nm2 = a1['rankNMinus2']

    # Also compute F_span MILP diagnostic (NOT used in upper[K]!)
    fspan_milp_diag = solve_char_cover_milp(ids, {p: frozenset(fspan[p]) for p in ids}, alphabet)

    # Assemble per-budget lower ends (forward monotone) and solver-free upper ends (backward monotone)
    raw_upper = []
    dual_certs = {}
    for k in range(width + 1):
        cands = []
        if k <= 1:
            cands.append((0, 'trivial (length >= 150, >= 2 chars)'))
        else:
            cands.append((n, 'cohort size'))
            cands.append((min(n, k + whole_nullity), f'whole-program rank nullity (nu={whole_nullity})'))
            elig = [p for p in ids if prank[p] <= k]
            cands.append((len(elig), 'per-program forced-block rank'))
            ub_dual, cert = solve_fspan_lp_dual(elig, fspan, alphabet, k)
            cands.append((ub_dual, 'F_span certified LP dual'))
            if ub_dual < min(c[0] for c in cands[:-1]):
                dual_certs[str(k)] = cert
            if k < r_full:
                cands.append((n - 1, f'full cohort forced-block rank ({r_full})'))
            if k < r_nm1:
                cands.append((n - 2, f'(N-1) subset forced-block rank ({r_nm1})'))
            if r_nm2 is not None and k < r_nm2:
                cands.append((n - 3, f'(N-2) subset forced-block rank ({r_nm2})'))
        ub_val, ub_src = min(cands, key=lambda x: x[0])
        raw_upper.append([ub_val, ub_src])

    # Backward monotonicity on upper bounds (sound because C_W(K) <= C_W(K+1))
    for k in range(width - 1, -1, -1):
        if raw_upper[k + 1][0] < raw_upper[k][0]:
            raw_upper[k] = [raw_upper[k + 1][0], f'monotone from K={k + 1} ({raw_upper[k + 1][1]})']

    # Forward monotonicity on lower ends (a dictionary of <= K entries is also valid at K+1)
    stored_dicts = {}
    rows = []
    cur_lower = 0
    cur_dict_key = None
    for k in range(width + 1):
        if k in best and best[k][0] > cur_lower:
            cnt, label, wset, sp = best[k]
            cur_lower = cnt
            cur_dict_key = f'd_{k}'
            stored_dicts[cur_dict_key] = {
                'entryCount': len(wset),
                'multiCharacterEntries': sum(1 for w in wset if len(w) > 1),
                'source': label,
                'entries': sorted(w.decode('ascii') for w in wset),
                'spellsCount': len(sp),
                'spells': sp,
            }
        sc = single_sets[str(k)]['spells']
        ub_val, ub_src = raw_upper[k]
        assert sc <= cur_lower <= ub_val, f'{cid} K={k}: invariant violated sc={sc} lo={cur_lower} ub={ub_val}'
        rows.append({
            'slots': k,
            'normSlots': round(k / width, 6),
            'singleCharacters': sc,
            'lower': cur_lower,
            'upper': ub_val,
            'exact': cur_lower == ub_val,
            'width': ub_val - cur_lower,
            'lowerDictionary': cur_dict_key,
            'upperSource': ub_src,
            'fspanMilpDiagnostic': min(fspan_milp_diag[k][0], sum(1 for p in ids if prank[p] <= k)),
        })

    # Character-set sharing statistics (pairwise Jaccard overlap + per-program alphabet size)
    char_sets = [need_chars[p] for p in ids]
    jaccards = []
    for i in range(n):
        si = char_sets[i]
        for j in range(i + 1, n):
            sj = char_sets[j]
            jaccards.append(len(si & sj) / len(si | sj))
    prog_alpha_sizes = sorted(len(s) for s in char_sets)

    # Coverage thresholds (25%, 50%, 75%) reported as intervals [K_lo, K_hi]
    thresholds = {}
    for pct in (25, 50, 75):
        target = math.ceil(n * pct / 100.0)
        k_lo = next(r['slots'] for r in rows if r['upper'] >= target)
        k_hi = next(r['slots'] for r in rows if r['lower'] >= target)
        k_ch = next(r['slots'] for r in rows if r['singleCharacters'] >= target)
        thresholds[f'p{pct}'] = {
            'targetPrograms': target,
            'slotsLo': k_lo,
            'slotsHi': k_hi,
            'normLo': round(k_lo / width, 4),
            'normHi': round(k_hi / width, 4),
            'singleCharSlots': k_ch,
            'singleCharNorm': round(k_ch / width, 4),
        }

    # Summary stats
    widths = [r['width'] for r in rows]
    exact_cnt = sum(1 for r in rows if r['exact'])
    within2_cnt = sum(1 for r in rows if r['width'] <= 2)
    wide5_cnt = sum(1 for r in rows if r['width'] > 0.05 * n)
    lifts = [r['lower'] - r['singleCharacters'] for r in rows]
    first_w = next((r['slots'] for r in rows if r['lower'] >= 1), None)
    first_c = next((r['slots'] for r in rows if r['singleCharacters'] >= 1), None)

    elapsed = round(time.monotonic() - t0, 2)
    return {
        'cohortId': cid,
        'family': cohort['family'],
        'role': cohort['role'],
        'split': cohort['split'],
        'size': n,
        'alphabetSize': width,
        'alphabet': bytes(alphabet).decode('ascii'),
        'totalBytes': sum(len(s) for s in whole_list),
        'primesAgree': primes_agree,
        'algebra': {
            'wholeRank': a1['wholeRank'],
            'wholeNullity': whole_nullity,
            'rankFull': r_full,
            'rankNMinus1': r_nm1,
            'rankNMinus2': r_nm2,
            'medianProgBlockRank': int(np.median(list(prank.values()))),
            'medianFspanSize': int(np.median([len(v) for v in fspan.values()])),
            'meanCharJaccard': round(float(np.mean(jaccards)), 4),
            'medianProgAlphabet': prog_alpha_sizes[n // 2],
            'iqrProgAlphabet': [prog_alpha_sizes[n // 4], prog_alpha_sizes[3 * n // 4]],
        },
        'summary': {
            'exactBudgets': exact_cnt,
            'totalBudgets': width + 1,
            'within2Budgets': within2_cnt,
            'wideOver5PctBudgets': wide5_cnt,
            'medianIntervalWidth': float(np.median(widths)),
            'maxIntervalWidth': int(max(widths)),
            'maxFragmentLift': int(max(lifts)),
            'maxFragmentLiftPct': round(100.0 * max(lifts) / n, 2),
            'budgetsWithFragmentLift': sum(1 for x in lifts if x > 0),
            'firstProgramSlotsWitnessed': first_w,
            'firstProgramSlotsSingleChar': first_c,
            'seconds': elapsed,
        },
        'thresholds': thresholds,
        'rows': rows,
        'singleCharacterSets': single_sets,
        'dictionaries': stored_dicts,
        'dualCertificates': dual_certs,
    }


# --------------------------------------------------------------------------- out-of-sample curve analysis
GRID = [round(i * 0.02, 2) for i in range(51)]


def sample_curve(cohort_res, field):
    n = cohort_res['size']
    w = cohort_res['alphabetSize']
    ys = [r[field] / n for r in cohort_res['rows']]
    out = []
    for x in GRID:
        k = min(w, max(0, int(round(x * w))))
        out.append(ys[k])
    return np.array(out)


def fit_logistic(xs, ys):
    def loss(params):
        a, x0 = params
        pred = 1.0 / (1.0 + np.exp(-np.clip(a * (xs - x0), -40, 40)))
        return float(np.mean((pred - ys) ** 2))
    res = minimize(loss, x0=[10.0, 0.7], bounds=[(0.1, 100.0), (0.0, 1.2)], method='L-BFGS-B')
    a, x0 = float(res.x[0]), float(res.x[1])
    return a, x0


def eval_logistic(xs, a, x0):
    return 1.0 / (1.0 + np.exp(-np.clip(a * (xs - x0), -40, 40)))


def interval_violation_mae(pred, lo, hi):
    viol = np.maximum(0.0, lo - pred) + np.maximum(0.0, pred - hi)
    return float(np.mean(viol))


def out_of_sample_analysis(cohort_results):
    by_id = {c['cohortId']: c for c in cohort_results}
    xs = np.array(GRID)
    pairs = []
    # 1. Same-family same-size: 40a->40b, 80a->80b, 160a->160b
    # 2. Same-family cross-size: 40a->80b, 40a->160b, 80a->40b, 80a->160b, 160a->40b, 160a->80b
    # 3. Cross-family: J-80-a -> P-80-b, P-80-a -> J-80-b, J-160-a -> P-160-b, P-160-a -> J-160-b
    eval_specs = [
        ('same-family-same-size', 'J-40-a', 'J-40-b'),
        ('same-family-same-size', 'J-80-a', 'J-80-b'),
        ('same-family-same-size', 'J-160-a', 'J-160-b'),
        ('same-family-same-size', 'P-40-a', 'P-40-b'),
        ('same-family-same-size', 'P-80-a', 'P-80-b'),
        ('same-family-same-size', 'P-160-a', 'P-160-b'),
        ('same-family-cross-size', 'J-40-a', 'J-80-b'),
        ('same-family-cross-size', 'J-40-a', 'J-160-b'),
        ('same-family-cross-size', 'J-80-a', 'J-160-b'),
        ('same-family-cross-size', 'J-160-a', 'J-40-b'),
        ('same-family-cross-size', 'P-40-a', 'P-80-b'),
        ('same-family-cross-size', 'P-40-a', 'P-160-b'),
        ('same-family-cross-size', 'P-80-a', 'P-160-b'),
        ('same-family-cross-size', 'P-160-a', 'P-40-b'),
        ('cross-family', 'J-40-a', 'P-40-b'),
        ('cross-family', 'P-40-a', 'J-40-b'),
        ('cross-family', 'J-80-a', 'P-80-b'),
        ('cross-family', 'P-80-a', 'J-80-b'),
        ('cross-family', 'J-160-a', 'P-160-b'),
        ('cross-family', 'P-160-a', 'J-160-b'),
    ]
    for kind, tr_id, te_id in eval_specs:
        tr, te = by_id[tr_id], by_id[te_id]
        y_tr_char = sample_curve(tr, 'singleCharacters')
        y_tr_lo = sample_curve(tr, 'lower')
        y_te_char = sample_curve(te, 'singleCharacters')
        y_te_lo = sample_curve(te, 'lower')
        y_te_hi = sample_curve(te, 'upper')

        a_c, x0_c = fit_logistic(xs, y_tr_char)
        pred_log_char = eval_logistic(xs, a_c, x0_c)

        a_l, x0_l = fit_logistic(xs, y_tr_lo)
        pred_log_lo = eval_logistic(xs, a_l, x0_l)

        pairs.append({
            'regime': kind,
            'train': tr_id,
            'test': te_id,
            'logisticOnChar_vs_testChar_MAE': round(float(np.mean(np.abs(pred_log_char - y_te_char))), 4),
            'monotoneOnChar_vs_testChar_MAE': round(float(np.mean(np.abs(y_tr_char - y_te_char))), 4),
            'logisticOnLower_vs_testLower_MAE': round(float(np.mean(np.abs(pred_log_lo - y_te_lo))), 4),
            'monotoneOnLower_vs_testLower_MAE': round(float(np.mean(np.abs(y_tr_lo - y_te_lo))), 4),
            'charBaseline_vs_testLower_MAE': round(float(np.mean(np.abs(y_tr_char - y_te_lo))), 4),
            'logisticOnLower_intervalViolation_MAE': round(interval_violation_mae(pred_log_lo, y_te_lo, y_te_hi), 4),
            'monotoneOnLower_intervalViolation_MAE': round(interval_violation_mae(y_tr_lo, y_te_lo, y_te_hi), 4),
            'logisticParamsLower': {'a': round(a_l, 3), 'x0': round(x0_l, 4)},
        })
    return pairs


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cohorts.json')
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'results.json')
    cohorts_sha = hashlib.sha256(open(in_path, 'rb').read()).hexdigest()
    data = json.load(open(in_path, 'r', encoding='utf-8'))

    t_all = time.monotonic()
    cohort_results = []
    for cohort in data['cohorts']:
        res = evaluate_cohort(cohort)
        cohort_results.append(res)
        s = res['summary']
        th50 = res['thresholds']['p50']
        print(
            f"{res['cohortId']:15s} n={res['size']:3d} |Sigma|={res['alphabetSize']:2d} "
            f"exact={s['exactBudgets']:2d}/{s['totalBudgets']:2d} "
            f"p50=[{th50['slotsLo']},{th50['slotsHi']}] (char={th50['singleCharSlots']}) "
            f"maxLift={s['maxFragmentLift']:2d} ({s['maxFragmentLiftPct']:4.1f}%) "
            f"medW={s['medianIntervalWidth']:4.1f} t={s['seconds']:5.1f}s",
            flush=True,
        )

    oos = out_of_sample_analysis(cohort_results)
    out = {
        'cohortsSha256': cohorts_sha,
        'seed': data['seed'],
        'rule': 'W (single chars + substrings <= 160 bytes in >= 2 programs; no whole program)',
        'primes': PRIMES,
        'dualScale': DUAL_SCALE,
        'totalSeconds': round(time.monotonic() - t_all, 2),
        'cohorts': cohort_results,
        'outOfSample': oos,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    h = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    print(f'Wrote {out_path} ({os.path.getsize(out_path):,} bytes, sha256={h}) in {out["totalSeconds"]}s')


if __name__ == '__main__':
    main()
