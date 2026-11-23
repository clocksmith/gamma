#!/usr/bin/env python3
"""Pre-registered slots K x max entry length L sweep on frozen matched80 compact.

Reads the 80 compact programs directly from Gamma commit 59ff04415ff2afd04ff2ed451340f4f02852bf18
via git show, sweeps L in [1, 2, 4, 8, 16, 32, 160] across K in 0..92, and records:
  - deterministic frequency-picked baselines (freqOcc, freqDoc, charFreqDoc);
  - exact single-character MILP optimum (replayed);
  - best verified W(L)-legal lower-end dictionaries (replayed byte-for-byte);
  - 100% solver-free proven upper bounds verified in two prime fields:
      * K in {0, 1} -> 0
      * exact unrestricted ceiling C_U(K)
      * per-program forced-block rank + L-capped character-capacity filter
      * F_span exact integer-certified LP dual
      * L-capped character-capacity exact integer-certified LP dual
      * tail subset forced-block ranks r_80(L), r_79(L), r_78(L)
      * monotonicity in K and L.

Usage:
    python3 -B run_length_sweep.py /path/to/gamma [results.json] [length-sweep.csv]
"""
import collections
import csv
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix, lil_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
PIN = '59ff04415ff2afd04ff2ed451340f4f02852bf18'
ROOT = 'projects/algorithm_solver/literals/'
LENGTHS = [1, 2, 4, 8, 16, 32, 160]
PRIMES = ((1_000_000_007, 2), (998_244_353, 3))
DUAL_SCALE = 1_000_000


def load_cohort(repo):
    def blob(path):
        return subprocess.check_output(['git', '-C', repo, 'show', f'{PIN}:{ROOT}{path}'])

    ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
    wanted = set(ids)
    manifest = json.loads(blob('scale-v2/generated/manifest.json'))['rows']
    sources = {
        r['id']: blob('scale-v2/generated/' + r['file'])
        for r in manifest
        if r['variant'] == 'compact' and r['id'] in wanted
    }
    assert len(sources) == 80 and len(set(sources.values())) == 80
    return ids, sources


def unrestricted_exact(k):
    return 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1 if k <= 79 else 80


def is_legal_wl(words, max_len, whole_list, whole_set):
    for w in words:
        if not w or len(w) > max_len or w in whole_set:
            return False
        if len(w) > 1:
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


def compute_shared_len_and_counts(ids, sources, max_cap=160):
    """Compute longest shared length <= max_cap at each (p, i) and exact (doc_freq, total_occ) of all W(max_cap) entries."""
    whole_set = set(sources.values())
    shared_len = {p: [0] * len(sources[p]) for p in ids}
    doc_freq = {}
    total_occ = {}

    # Length 1: all single characters in cohort (all legal because every program has length >= 60)
    for p in ids:
        s = sources[p]
        seen = set()
        for ch in s:
            w = bytes([ch])
            total_occ[w] = total_occ.get(w, 0) + 1
            seen.add(w)
        for w in seen:
            doc_freq[w] = doc_freq.get(w, 0) + 1

    alive = [(p, i) for p in ids for i in range(len(sources[p]))]
    for length in range(1, max_cap + 1):
        occ_by_sub = collections.defaultdict(int)
        owners_by_sub = collections.defaultdict(set)
        live = [(p, i) for p, i in alive if i + length <= len(sources[p])]
        for p, i in live:
            sub = sources[p][i:i + length]
            occ_by_sub[sub] += 1
            owners_by_sub[sub].add(p)
        multi = {sub for sub, owners in owners_by_sub.items() if len(owners) >= 2}
        if not multi:
            break
        if length >= 2:
            for sub in multi:
                if sub not in whole_set:
                    doc_freq[sub] = len(owners_by_sub[sub])
                    total_occ[sub] = occ_by_sub[sub]
        next_alive = []
        for p, i in live:
            sub = sources[p][i:i + length]
            if sub in multi:
                shared_len[p][i] = length
                next_alive.append((p, i))
        alive = next_alive
    return shared_len, doc_freq, total_occ


# --------------------------------------------------------------------------- finite-field algebra
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


def compute_forced_blocks_wl(ids, sources, max_len):
    if max_len == 1:
        return {p: [bytes([ch]) for ch in sorted(set(sources[p]))] for p in ids}
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


def algebra_one_prime(ids, alphabet, blocks_by_prog, mod, base):
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    basis, prank, fspan = {}, {}, {}
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

    n = len(ids)
    r_full = stack_rank([basis[p] for p in ids])

    pref = [np.zeros((0, width), dtype=np.int64)] * (n + 1)
    for i in range(n):
        pref[i + 1] = rref_matrix(np.vstack([pref[i], basis[ids[i]]]), mod) if pref[i].shape[0] else basis[ids[i]]
    suff = [np.zeros((0, width), dtype=np.int64)] * (n + 1)
    for i in range(n - 1, -1, -1):
        suff[i] = rref_matrix(np.vstack([basis[ids[i]], suff[i + 1]]), mod) if suff[i + 1].shape[0] else basis[ids[i]]

    r_nm1 = min(stack_rank([pref[i], suff[i + 1]]) for i in range(n))
    r_nm2 = width
    for i in range(n):
        cur_pref = pref[i]
        for j in range(i + 1, n):
            rk = width if (cur_pref.shape[0] == width or suff[j + 1].shape[0] == width) else stack_rank([cur_pref, suff[j + 1]])
            if rk < r_nm2:
                r_nm2 = rk
            if cur_pref.shape[0] < width:
                cur_pref = rref_matrix(np.vstack([cur_pref, basis[ids[j]]]), mod) if cur_pref.shape[0] else basis[ids[j]]

    return {
        'prank': prank,
        'fspan': fspan,
        'rankFull': r_full,
        'rankNMinus1': r_nm1,
        'rankNMinus2': r_nm2,
    }


# --------------------------------------------------------------------------- LP / MILP helpers
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
    n_p = len(elig_ids)
    if n_p == 0:
        return 0, {'kind': 'fspan', 'scale': DUAL_SCALE, 'mu': 0, 'alpha': []}
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    c = np.zeros(width + n_p)
    c[width:] = -1.0
    rows, cols, vals, edge_meta = [], [], [], []
    ri = 0
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
    assert res.status == 0, f'fspan LP failed at K={budget}: {res.message}'

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
    return int(cert_ub), {'kind': 'fspan', 'scale': DUAL_SCALE, 'mu': mu, 'alpha': alpha_entries}


def solve_lcap_lp_dual(elig_ids, u1_by_id, rem_by_id, alphabet, max_len, budget):
    r"""Exact integer-certified LP dual for the L-capped character-capacity relaxation.

    Primal: max sum_{p in E} z_p
      s.t. z_p - x_c <= 0          for c in U_1(p)
           z_p - x_c - y_c <= 0    for c in R(p) = chars(p) \ U_1(p)
           L * sum x_c + sum y_c <= L * K
           0 <= x_c, y_c, z_p <= 1.
    """
    n_p = len(elig_ids)
    if n_p == 0:
        return 0, {'kind': 'lcap', 'scale': DUAL_SCALE, 'maxLen': max_len, 'mu': 0, 'a': [], 'b': []}
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    # vars: x[0..W-1], y[W..2W-1], z[2W..2W+n_p-1]
    n_vars = 2 * width + n_p
    c = np.zeros(n_vars)
    c[2 * width:] = -1.0
    rows, cols, vals = [], [], []
    a_meta, b_meta = [], []
    ri = 0
    for pi, p in enumerate(elig_ids):
        for ch in sorted(u1_by_id[p]):
            rows.append(ri); cols.append(2 * width + pi); vals.append(1.0)
            rows.append(ri); cols.append(col_of[ch]); vals.append(-1.0)
            a_meta.append((ri, p, ch, pi))
            ri += 1
        for ch in sorted(rem_by_id[p]):
            rows.append(ri); cols.append(2 * width + pi); vals.append(1.0)
            rows.append(ri); cols.append(col_of[ch]); vals.append(-1.0)
            rows.append(ri); cols.append(width + col_of[ch]); vals.append(-1.0)
            b_meta.append((ri, p, ch, pi))
            ri += 1
    for ci in range(width):
        rows.append(ri); cols.append(ci); vals.append(float(max_len))
        rows.append(ri); cols.append(width + ci); vals.append(1.0)
    ub = np.zeros(ri + 1)
    ub[ri] = float(max_len * budget)
    A = coo_matrix((vals, (rows, cols)), shape=(ri + 1, n_vars)).tocsr()
    res = linprog(c, A_ub=A, b_ub=ub, bounds=(0, 1), method='highs')
    assert res.status == 0, f'lcap LP failed at L={max_len} K={budget}: {res.message}'

    duals = -res.ineqlin.marginals
    mu = max(0, int(round(duals[-1] * DUAL_SCALE)))
    a_entries, b_entries = [], []
    x_load = collections.Counter()
    y_load = collections.Counter()
    prog_load = collections.Counter()
    for ridx, p, ch, pi in a_meta:
        val = max(0, int(round(duals[ridx] * DUAL_SCALE)))
        if val > 0:
            a_entries.append([p, ch, val])
            x_load[ch] += val
            prog_load[pi] += val
    for ridx, p, ch, pi in b_meta:
        val = max(0, int(round(duals[ridx] * DUAL_SCALE)))
        if val > 0:
            b_entries.append([p, ch, val])
            x_load[ch] += val
            y_load[ch] += val
            prog_load[pi] += val
    gx_sum = sum(max(0, x_load[ch] - max_len * mu) for ch in x_load)
    gy_sum = sum(max(0, y_load[ch] - mu) for ch in y_load)
    beta_sum = sum(max(0, DUAL_SCALE - prog_load[pi]) for pi in range(n_p))
    cert_ub = (beta_sum + gx_sum + gy_sum + max_len * budget * mu) // DUAL_SCALE
    return int(cert_ub), {
        'kind': 'lcap',
        'scale': DUAL_SCALE,
        'maxLen': max_len,
        'mu': mu,
        'a': a_entries,
        'b': b_entries,
    }


# --------------------------------------------------------------------------- lower-end builders
def parse_cost_dp(s, shared_l, max_len, by_first, have, bias_single, bias_multi, len_bonus, whole_set):
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
        ml = min(shared_l[i], max_len, n - i)
        if ml >= 2:
            for j in range(i + 2, i + ml + 1):
                cm = fi + 1.0 + bias_multi - len_bonus * (j - i)
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


def compress_rare_char_clusters(subset_ids, sources, shared_len, max_len, whole_list, whole_set):
    if max_len < 2 or not subset_ids:
        return None
    sub_sources = {p: sources[p] for p in subset_ids}
    chars = sorted(set(b''.join(sub_sources.values())))
    char_occ = collections.defaultdict(list)
    for p in subset_ids:
        s = sources[p]
        for i, ch in enumerate(s):
            char_occ[ch].append((p, i))
    rare = [ch for ch in chars if len(char_occ[ch]) <= 16]
    if len(rare) < 2:
        return None
    rare_set = set(rare)
    cand_subs = collections.Counter()
    for p in subset_ids:
        s = sources[p]
        sl = shared_len[p]
        n = len(s)
        for i in range(n):
            ml = min(sl[i], max_len, n - i)
            if ml < 2:
                continue
            seg = s[i:i + ml]
            if len(rare_set.intersection(seg)) >= 2:
                idxs = [k for k, ch in enumerate(seg) if ch in rare_set]
                sub = seg[idxs[0]:idxs[-1] + 1]
                if 2 <= len(sub) <= max_len and sub not in whole_set:
                    cand_subs[sub] += 1
    if not cand_subs:
        return None
    current_chars = set(chars)
    added_frags = set()
    for sub, _ in cand_subs.most_common(96):
        sub_chars = set(sub) & current_chars
        if len(sub_chars) < 2:
            continue
        droppable = set()
        for ch in sub_chars:
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
            if is_legal_wl(trial, max_len, whole_list, whole_set):
                got = set(replay_spelled(trial, subset_ids, sources))
                if len(got) == len(subset_ids):
                    current_chars -= droppable
                    added_frags.add(sub)
    if not added_frags:
        return None
    return {bytes([c]) for c in current_chars} | added_frags


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 -B run_length_sweep.py /path/to/gamma [results.json] [length-sweep.csv]')
    repo = sys.argv[1]
    out_json = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'results.json')
    out_csv = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'length-sweep.csv')

    t_all = time.monotonic()
    ids, sources = load_cohort(repo)
    whole_list = [sources[p] for p in ids]
    whole_set = set(whole_list)
    alphabet = sorted(set(b''.join(whole_list)))
    width = len(alphabet)
    n = len(ids)
    assert width == 92 and n == 80

    # 1. Exact single-character optimum (replayed)
    need_chars = {p: frozenset(sources[p]) for p in ids}
    singles_milp = solve_char_cover_milp(ids, need_chars, alphabet)
    single_sets = {}
    for k in range(width + 1):
        opt, chosen = singles_milp[k]
        words = frozenset(bytes([c]) for c in chosen)
        sp = replay_spelled(words, ids, sources) if words else []
        assert len(sp) == opt
        single_sets[str(k)] = {'characters': bytes(chosen).decode('latin-1'), 'spells': opt}

    # 2. Shared lengths & exact occurrence/document counts up to max L=160
    shared_len, doc_freq, total_occ = compute_shared_len_and_counts(ids, sources, max(LENGTHS))

    # Single-character frequency baseline (doc_freq DESC, total_occ DESC, bytes ASC)
    all_chars_ranked = sorted(
        [bytes([c]) for c in alphabet],
        key=lambda w: (-doc_freq[w], -total_occ[w], w),
    )
    char_freq_spelled = [0]
    for k in range(1, width + 1):
        char_freq_spelled.append(len(replay_spelled(all_chars_ranked[:k], ids, sources)))

    # 3. Precompute forced-block algebra in TWO prime fields for L=1 and L>=2
    alg_by_mode = {}
    u1_by_mode = {}
    rem_by_mode = {}
    for mode_l in (1, 2):
        blocks = compute_forced_blocks_wl(ids, sources, mode_l)
        u1 = {}
        rem = {}
        for p in ids:
            forced_singles = frozenset(b[0] for b in blocks[p] if len(b) == 1)
            u1[p] = forced_singles
            rem[p] = need_chars[p] - forced_singles
        u1_by_mode[mode_l] = u1
        rem_by_mode[mode_l] = rem
        p1 = algebra_one_prime(ids, alphabet, blocks, PRIMES[0][0], PRIMES[0][1])
        p2 = algebra_one_prime(ids, alphabet, blocks, PRIMES[1][0], PRIMES[1][1])
        alg_by_mode[mode_l] = (p1, p2, p1 == p2)

    # 4. Sweep L in ascending order; inherit verified dictionaries from smaller L
    prev_lower_dicts = {}  # k -> (cnt, wset)
    per_l_results = {}

    for max_len in LENGTHS:
        t0 = time.monotonic()
        mode_l = 1 if max_len == 1 else 2
        a1, a2, primes_agree = alg_by_mode[mode_l]
        u1 = u1_by_mode[mode_l]
        rem = rem_by_mode[mode_l]
        prank = a1['prank']
        fspan = a1['fspan']
        r_full = a1['rankFull']
        r_nm1 = a1['rankNMinus1']
        r_nm2 = a1['rankNMinus2']

        # Deterministic frequency-picked baselines for W(L)
        wl_vocab = [w for w in doc_freq if len(w) <= max_len]
        ranked_occ = sorted(wl_vocab, key=lambda w: (-total_occ[w], -doc_freq[w], len(w), w))
        ranked_doc = sorted(wl_vocab, key=lambda w: (-doc_freq[w], -total_occ[w], -len(w), w))
        freq_occ_top = ranked_occ[:width]
        freq_doc_top = ranked_doc[:width]
        assert is_legal_wl(freq_occ_top, max_len, whole_list, whole_set)
        assert is_legal_wl(freq_doc_top, max_len, whole_list, whole_set)

        freq_occ_curve = [0] + [len(replay_spelled(freq_occ_top[:k], ids, sources)) for k in range(1, width + 1)]
        freq_doc_curve = [0] + [len(replay_spelled(freq_doc_top[:k], ids, sources)) for k in range(1, width + 1)]

        # Best verified lower-end dictionaries
        best = {}

        def offer(words, label):
            wset = frozenset(words)
            if not wset or len(wset) > width:
                return
            if not is_legal_wl(wset, max_len, whole_list, whole_set):
                return
            sp = replay_spelled(wset, ids, sources)
            k = len(wset)
            cnt = len(sp)
            if cnt > best.get(k, (-1,))[0]:
                best[k] = (cnt, label, wset, sp)

        # Offer exact single-character sets
        for k in range(1, width + 1):
            chosen = single_sets[str(k)]['characters'].encode('latin-1')
            offer([bytes([c]) for c in chosen], 'single characters')

        # Offer inherited dictionaries from smaller L
        for k, (_, prev_wset) in prev_lower_dicts.items():
            offer(prev_wset, f'inherited from L<{max_len}')

        if max_len >= 2:
            # 8 deterministic greedy DP runs capped at max_len
            configs = [
                (0.0, 0.001, 0.0, None, 'greedy DP, single preferred'),
                (0.001, 0.0, 0.0, None, 'greedy DP, multi preferred'),
                (0.001, 0.0, 1e-4, None, 'greedy DP, longer multi preferred'),
                (0.0, 0.0, 0.0, f'L{max_len}/s0', 'greedy DP, tie seed 0'),
                (0.001, 0.0, 0.0, f'L{max_len}/s1', 'greedy DP, multi tie seed 1'),
                (0.0, 0.001, 0.0, f'L{max_len}/s2', 'greedy DP, single tie seed 2'),
                (0.001, 0.0, 2e-4, f'L{max_len}/s3', 'greedy DP, longer multi seed 3'),
                (0.002, 0.0, 5e-4, f'L{max_len}/s4', 'greedy DP, strong multi seed 4'),
            ]
            for bias_s, bias_m, len_b, seed, label in configs:
                rng = random.Random(seed) if seed is not None else None
                have = set()
                group = set()
                by_first = collections.defaultdict(list)
                while len(group) < n and len(have) < width:
                    options = []
                    for p in ids:
                        if p in group:
                            continue
                        new = parse_cost_dp(
                            sources[p], shared_len[p], max_len, by_first, have, bias_s, bias_m, len_b, whole_set
                        )
                        tie = rng.random() if rng else 0.0
                        options.append((len(new), tie, p, new))
                    _, _, p, new = min(options)
                    if any(w in whole_set or len(w) > max_len for w in new):
                        new = {w for w in new if w not in whole_set and len(w) <= max_len} | {
                            bytes([c]) for w in new if (w in whole_set or len(w) > max_len) for c in w
                        }
                    for w in new:
                        have.add(w)
                        by_first[w[0]].append(w)
                    group.add(p)
                    if len(have) <= width:
                        offer(have, label)

            # Rare-character cluster compression across single-char subsets (+0, +1, +2)
            tested = set()
            for k in range(1, width + 1):
                chosen = frozenset(single_sets[str(k)]['characters'].encode('latin-1'))
                sub_ids = tuple(p for p in ids if need_chars[p] <= chosen)
                if sub_ids and sub_ids not in tested:
                    tested.add(sub_ids)
                    comp = compress_rare_char_clusters(list(sub_ids), sources, shared_len, max_len, whole_list, whole_set)
                    if comp is not None:
                        offer(comp, 'rare-char cluster compression')
                uncov = [p for p in ids if not (need_chars[p] <= chosen)]
                uncov.sort(key=lambda p: (len(need_chars[p] - chosen), p))
                for extra_cnt in (1, 2):
                    if len(uncov) >= extra_cnt:
                        sub_plus = tuple(sorted(set(sub_ids) | set(uncov[:extra_cnt])))
                        if sub_plus not in tested:
                            tested.add(sub_plus)
                            comp = compress_rare_char_clusters(
                                list(sub_plus), sources, shared_len, max_len, whole_list, whole_set
                            )
                            if comp is not None:
                                offer(comp, f'rare-char cluster compression (+{extra_cnt})')

        # Solver-free proven upper bounds
        raw_upper = []
        dual_certs = {}
        for k in range(width + 1):
            if k <= 1:
                raw_upper.append([0, 'trivial (length >= 60, >= 2 chars)'])
                continue
            cu = unrestricted_exact(k)
            elig = [
                p for p in ids
                if prank[p] <= k and (len(u1[p]) + math.ceil(len(rem[p]) / max_len)) <= k
            ]
            cands = [
                (cu, 'unrestricted exact C_U(K)'),
                (len(elig), 'per-program rank + L-cap filter'),
            ]
            if k < r_full:
                cands.append((n - 1, f'full forced-block rank ({r_full})'))
            if k < r_nm1:
                cands.append((n - 2, f'79-subset forced-block rank ({r_nm1})'))
            if k < r_nm2:
                cands.append((n - 3, f'78-subset forced-block rank ({r_nm2})'))
            base_min = min(c[0] for c in cands)

            ub_fspan, cert_fspan = solve_fspan_lp_dual(elig, fspan, alphabet, k)
            ub_lcap, cert_lcap = solve_lcap_lp_dual(elig, u1, rem, alphabet, max_len, k)
            cands.append((ub_fspan, 'F_span certified LP dual'))
            cands.append((ub_lcap, 'L-cap certified LP dual'))

            ub_val, ub_src = min(cands, key=lambda x: x[0])
            if ub_val < base_min:
                if ub_lcap <= ub_fspan and ub_lcap == ub_val:
                    dual_certs[str(k)] = cert_lcap
                else:
                    dual_certs[str(k)] = cert_fspan
            raw_upper.append([ub_val, ub_src])

        # Backward monotonicity in K
        for k in range(width - 1, -1, -1):
            if raw_upper[k + 1][0] < raw_upper[k][0]:
                raw_upper[k] = [raw_upper[k + 1][0], f'monotone from K={k + 1}']

        # Forward monotonicity on lower ends + store dictionaries
        stored_dicts = {}
        rows = []
        cur_lower = 0
        cur_dict_key = None
        next_prev = {}
        for k in range(width + 1):
            if k in best and best[k][0] > cur_lower:
                cnt, label, wset, sp = best[k]
                cur_lower = cnt
                cur_dict_key = f'L{max_len}_d{k}'
                stored_dicts[cur_dict_key] = {
                    'entryCount': len(wset),
                    'multiCharacterEntries': sum(1 for w in wset if len(w) > 1),
                    'maxEntryLen': max(len(w) for w in wset),
                    'source': label,
                    'entries': sorted(w.decode('latin-1') for w in wset),
                    'spellsCount': len(sp),
                    'spells': sp,
                }
                next_prev[k] = (cnt, wset)
            sc = single_sets[str(k)]['spells']
            ub_val, ub_src = raw_upper[k]
            assert sc <= cur_lower <= ub_val, f'L={max_len} K={k}: sc={sc} lo={cur_lower} ub={ub_val}'
            rows.append({
                'maxLen': max_len,
                'slots': k,
                'singleCharOpt': sc,
                'charFreqDoc': char_freq_spelled[k],
                'freqOcc': freq_occ_curve[k],
                'freqDoc': freq_doc_curve[k],
                'lower': cur_lower,
                'upper': ub_val,
                'unrestrictedCeiling': unrestricted_exact(k),
                'exact': cur_lower == ub_val,
                'width': ub_val - cur_lower,
                'lowerDictionary': cur_dict_key,
                'upperSource': ub_src,
            })

        prev_lower_dicts = next_prev
        elapsed = round(time.monotonic() - t0, 2)
        per_l_results[max_len] = {
            'maxLen': max_len,
            'legalVocabSize': len(wl_vocab),
            'primesAgree': primes_agree,
            'algebra': {
                'rankFull': r_full,
                'rankNMinus1': r_nm1,
                'rankNMinus2': r_nm2,
            },
            'freqOccTop92': [w.decode('latin-1') for w in freq_occ_top],
            'freqDocTop92': [w.decode('latin-1') for w in freq_doc_top],
            'rows': rows,
            'dictionaries': stored_dicts,
            'dualCertificates': dual_certs,
            'seconds': elapsed,
        }

    # Cross-L upper bound monotonicity (upper(K, L) <= upper(K, L_next) for L < L_next)
    for idx in range(len(LENGTHS) - 2, -1, -1):
        l_cur = LENGTHS[idx]
        l_nxt = LENGTHS[idx + 1]
        r_cur = per_l_results[l_cur]['rows']
        r_nxt = per_l_results[l_nxt]['rows']
        for k in range(width + 1):
            if r_nxt[k]['upper'] < r_cur[k]['upper']:
                r_cur[k]['upper'] = r_nxt[k]['upper']
                r_cur[k]['upperSource'] = f'monotone from L={l_nxt}'
                r_cur[k]['exact'] = (r_cur[k]['lower'] == r_cur[k]['upper'])
                r_cur[k]['width'] = r_cur[k]['upper'] - r_cur[k]['lower']

    # Print summary per L
    for max_len in LENGTHS:
        res = per_l_results[max_len]
        rows = res['rows']
        k_first = next((r['slots'] for r in rows if r['lower'] >= 1), None)
        exact_cnt = sum(1 for r in rows if r['exact'])
        mean_lo = sum(r['lower'] for r in rows) / len(rows)
        med_w = float(np.median([r['width'] for r in rows]))
        r64 = rows[64]
        r82 = rows[82]
        print(
            f"L={max_len:3d} vocab={res['legalVocabSize']:5d} exact={exact_cnt:2d}/93 "
            f"K_first={k_first:2d} meanLo={mean_lo:5.2f} medW={med_w:4.1f} "
            f"K64=[{r64['lower']},{r64['upper']}](occ={r64['freqOcc']},doc={r64['freqDoc']}) "
            f"K82=[{r82['lower']},{r82['upper']}] t={res['seconds']:5.2f}s",
            flush=True,
        )

    out = {
        'pin': PIN,
        'cohort': 'matched80-compact',
        'programCount': n,
        'alphabetSize': width,
        'lengths': LENGTHS,
        'primes': PRIMES,
        'dualScale': DUAL_SCALE,
        'totalSeconds': round(time.monotonic() - t_all, 2),
        'charFreqRanked': [w.decode('latin-1') for w in all_chars_ranked],
        'singleCharacterSets': single_sets,
        'sweeps': [per_l_results[L] for L in LENGTHS],
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    fieldnames = [
        'maxLen', 'slots', 'singleCharOpt', 'charFreqDoc', 'freqOcc', 'freqDoc',
        'lower', 'upper', 'unrestrictedCeiling', 'exact', 'width', 'lowerDictionary', 'upperSource',
    ]
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for L in LENGTHS:
            for r in per_l_results[L]['rows']:
                w.writerow({k: r[k] for k in fieldnames})

    h_json = hashlib.sha256(open(out_json, 'rb').read()).hexdigest()
    h_csv = hashlib.sha256(open(out_csv, 'rb').read()).hexdigest()
    print(f'Wrote {out_json} ({os.path.getsize(out_json):,} bytes, sha256={h_json})')
    print(f'Wrote {out_csv} ({os.path.getsize(out_csv):,} bytes, sha256={h_csv}) in {out["totalSeconds"]}s')


if __name__ == '__main__':
    main()
