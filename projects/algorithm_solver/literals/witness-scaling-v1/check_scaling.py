#!/usr/bin/env python3
"""Independent solver-free verifier for witness-scaling-v1. Python 3.10+ and numpy only; no solver.

Verifies every cohort in results.json directly from cohorts.json:
  - checks cohorts.json SHA-256 matches results.json;
  - checks every stored dictionary for W-legality (nonempty, not a whole program, single byte or
    <= 160 bytes occurring in >= 2 programs of the cohort) and replays it byte-for-byte;
  - replays every stored single-character set;
  - recomputes forced cuts, whole-program rank/nullity, per-program forced-block rank, forced
    unit-vector sets F_span, full rank r_N, (N-1)-subset rank r_{N-1}, and (for N <= 80)
    (N-2)-subset rank r_{N-2} in TWO prime fields;
  - checks every stored integer LP dual certificate on F_span using exact integer arithmetic;
  - verifies singleCharacters <= lower <= upper, monotonicity, exactness flags, and 25/50/75%
    threshold intervals at every budget.

    python3 -B check_scaling.py [cohorts.json] [results.json]
"""
import collections
import hashlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES_W = 160
PRIMES = ((1_000_000_007, 2), (998_244_353, 3))


def check(cond, msg):
    if not cond:
        raise SystemExit('FAILED: ' + msg)


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


def verify_dual_cert(cert, elig_ids, fspan, budget):
    scale = int(cert['scale'])
    mu = int(cert['mu'])
    check(scale > 0 and mu >= 0, 'invalid dual scale or mu')
    elig_set = set(elig_ids)
    char_load = collections.Counter()
    prog_load = collections.Counter()
    seen_edges = set()
    for p, ch, val in cert['alpha']:
        val = int(val)
        check(val >= 0, 'negative alpha in dual certificate')
        check(p in elig_set, f'dual edge references ineligible program {p}')
        check(ch in fspan[p], f'dual edge references non-forced char {ch} for {p}')
        key = (p, ch)
        check(key not in seen_edges, f'duplicate dual edge {key}')
        seen_edges.add(key)
        char_load[ch] += val
        prog_load[p] += val
    gamma_sum = sum(max(0, char_load[ch] - mu) for ch in char_load)
    beta_sum = sum(max(0, scale - prog_load[p]) for p in elig_ids)
    return (beta_sum + gamma_sum + mu * budget) // scale


def algebra_one_prime(ids, sources, alphabet, blocks_by_prog, mod, base, compute_n_minus_2):
    width = len(alphabet)
    col_of = {c: i for i, c in enumerate(alphabet)}
    whole_rank = len(rref_matrix([poly_vector(sources[p], col_of, width, mod, base) for p in ids], mod))
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
    r_nm2 = None
    if compute_n_minus_2:
        r_nm2 = width
        for i in range(n):
            cur_pref = pref[i]
            for j in range(i + 1, n):
                rk = width if (cur_pref.shape[0] == width or suff[j + 1].shape[0] == width) else stack_rank([cur_pref, suff[j + 1]])
                if rk < r_nm2:
                    r_nm2 = rk
                if cur_pref.shape[0] < width:
                    cur_pref = rref_matrix(np.vstack([cur_pref, basis[ids[j]]]), mod) if cur_pref.shape[0] else basis[ids[j]]
    return whole_rank, prank, fspan, r_full, r_nm1, r_nm2


def main():
    cohorts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cohorts.json')
    results_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'results.json')
    cohorts_sha = hashlib.sha256(open(cohorts_path, 'rb').read()).hexdigest()
    cohorts_data = json.load(open(cohorts_path, 'r', encoding='utf-8'))
    results_data = json.load(open(results_path, 'r', encoding='utf-8'))

    check(results_data['cohortsSha256'] == cohorts_sha, 'cohorts.json SHA-256 mismatch')
    by_id = {c['cohortId']: c for c in cohorts_data['cohorts']}
    check(len(results_data['cohorts']) == len(by_id), 'cohort count mismatch')

    total_dicts = 0
    total_duals = 0
    total_budgets = 0
    total_exact = 0

    for res in results_data['cohorts']:
        cid = res['cohortId']
        cohort = by_id[cid]
        ids = [p['id'] for p in cohort['programs']]
        sources = {p['id']: p['text'].encode('ascii') for p in cohort['programs']}
        whole_list = [sources[p] for p in ids]
        whole_set = set(whole_list)
        alphabet = sorted(set(b''.join(whole_list)))
        width = len(alphabet)
        n = len(ids)

        check(res['size'] == n and res['alphabetSize'] == width, f'{cid}: size or alphabet mismatch')
        check(all(len(s) >= 2 and len(set(s)) >= 2 for s in whole_list), f'{cid}: trivial program found')

        # 1. Verify all stored dictionaries: W-legality and byte-for-byte replay
        replayed = {}
        for dkey, d in res['dictionaries'].items():
            words = [w.encode('ascii') for w in d['entries']]
            check(len(set(words)) == len(words) == d['entryCount'], f'{cid} {dkey}: entryCount')
            check(sum(1 for w in words if len(w) > 1) == d['multiCharacterEntries'], f'{cid} {dkey}: multiCount')
            for w in words:
                check(len(w) >= 1 and w not in whole_set, f'{cid} {dkey}: empty or whole program')
                if len(w) > 1:
                    check(len(w) <= MAX_BYTES_W, f'{cid} {dkey}: exceeds 160 bytes')
                    check(sum(1 for s in whole_list if w in s) >= 2, f'{cid} {dkey}: occurs in < 2 programs')
            got = replay_spelled(words, ids, sources)
            check(got == d['spells'] and len(got) == d['spellsCount'], f'{cid} {dkey}: replay mismatch')
            replayed[dkey] = (len(words), len(got))
            total_dicts += 1

        # 2. Verify all single-character sets replay
        for k in range(width + 1):
            sc = res['singleCharacterSets'][str(k)]
            chars = sc['characters'].encode('ascii')
            check(len(set(chars)) == len(chars) <= k, f'{cid} K={k}: single char count')
            cset = frozenset(chars)
            got = sum(1 for s in whole_list if frozenset(s) <= cset)
            check(got == sc['spells'], f'{cid} K={k}: single char replay mismatch')

        # 3. Recompute forced blocks & algebraic bounds in TWO prime fields
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

        p1 = algebra_one_prime(ids, sources, alphabet, blocks_by_prog, PRIMES[0][0], PRIMES[0][1], n <= 80)
        p2 = algebra_one_prime(ids, sources, alphabet, blocks_by_prog, PRIMES[1][0], PRIMES[1][1], n <= 80)
        whole_rank, prank, fspan, r_full, r_nm1, r_nm2 = p1
        check(res['algebra']['wholeRank'] == whole_rank, f'{cid}: wholeRank mismatch')
        check(res['algebra']['rankFull'] == r_full, f'{cid}: rankFull mismatch')
        check(res['algebra']['rankNMinus1'] == r_nm1, f'{cid}: rankNMinus1 mismatch')
        check(res['algebra']['rankNMinus2'] == r_nm2, f'{cid}: rankNMinus2 mismatch')
        primes_agree = (p1 == p2)
        check(res['primesAgree'] == primes_agree, f'{cid}: primesAgree flag mismatch')

        # 4. Independently verify solver-free upper bounds at every budget
        nullity = n - whole_rank
        recomputed_ub = []
        for k in range(width + 1):
            if k <= 1:
                ub = 0
            else:
                elig = [p for p in ids if prank[p] <= k]
                cands = [n, min(n, k + nullity), len(elig)]
                if str(k) in res['dualCertificates']:
                    ub_dual = verify_dual_cert(res['dualCertificates'][str(k)], elig, fspan, k)
                    cands.append(ub_dual)
                    total_duals += 1
                if k < r_full:
                    cands.append(n - 1)
                if k < r_nm1:
                    cands.append(n - 2)
                if r_nm2 is not None and k < r_nm2:
                    cands.append(n - 3)
                ub = min(cands)
            recomputed_ub.append(ub)
        for k in range(width - 1, -1, -1):
            if recomputed_ub[k + 1] < recomputed_ub[k]:
                recomputed_ub[k] = recomputed_ub[k + 1]

        # 5. Check every budget row
        rows = res['rows']
        check([r['slots'] for r in rows] == list(range(width + 1)), f'{cid}: slot sequence')
        prev_lo, prev_ub = 0, 0
        for r in rows:
            k = r['slots']
            if r['lowerDictionary'] is None:
                check(r['lower'] == 0, f'{cid} K={k}: lower without dict')
            else:
                ec, spc = replayed[r['lowerDictionary']]
                check(ec <= k and spc == r['lower'], f'{cid} K={k}: lower dict mismatch')
            check(r['singleCharacters'] == res['singleCharacterSets'][str(k)]['spells'], f'{cid} K={k}: singleCharacters mismatch')
            check(r['upper'] == recomputed_ub[k], f'{cid} K={k}: upper {r["upper"]} != verified {recomputed_ub[k]}')
            check(r['singleCharacters'] <= r['lower'] <= r['upper'], f'{cid} K={k}: ordering violated')
            check(r['exact'] == (r['lower'] == r['upper']), f'{cid} K={k}: exact flag')
            check(r['width'] == r['upper'] - r['lower'], f'{cid} K={k}: width')
            check(r['lower'] >= prev_lo and r['upper'] >= prev_ub, f'{cid} K={k}: monotonicity violated')
            prev_lo, prev_ub = r['lower'], r['upper']
            total_budgets += 1
            total_exact += int(r['exact'])

        # 6. Verify 25/50/75% threshold intervals
        for pct in (25, 50, 75):
            target = math.ceil(n * pct / 100.0)
            th = res['thresholds'][f'p{pct}']
            check(th['targetPrograms'] == target, f'{cid} p{pct}: target')
            check(th['slotsLo'] == next(r['slots'] for r in rows if r['upper'] >= target), f'{cid} p{pct}: slotsLo')
            check(th['slotsHi'] == next(r['slots'] for r in rows if r['lower'] >= target), f'{cid} p{pct}: slotsHi')
            check(th['singleCharSlots'] == next(r['slots'] for r in rows if r['singleCharacters'] >= target), f'{cid} p{pct}: singleCharSlots')

        print(f"OK {cid:15s} n={n:3d} |Sigma|={width:2d} exact={res['summary']['exactBudgets']:2d}/{width+1:2d} primesAgree={primes_agree}")

    print(
        f"ALL VERIFIED (solver-free): {len(results_data['cohorts'])} cohorts, {total_budgets} budgets "
        f"({total_exact} exact), {total_dicts} dictionaries replayed, {total_duals} integer LP duals checked."
    )


if __name__ == '__main__':
    main()
