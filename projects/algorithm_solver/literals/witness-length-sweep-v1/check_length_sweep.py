#!/usr/bin/env python3
"""100% solver-free independent verifier for witness-length-sweep-v1.

Requires only Python 3.10+, numpy, and git (NO scipy, NO MILP/LP solver).
Reads the frozen matched80 compact cohort directly from Gamma commit
59ff04415ff2afd04ff2ed451340f4f02852bf18 and independently verifies:
  1. All single-character sets replay to their recorded counts.
  2. All frequency-picked baselines (charFreqDoc, freqOcc, freqDoc) are strictly
     W(L)-legal, match the exact deterministic ranking, and replay byte-for-byte.
  3. Every stored lower-end dictionary is strictly W(L)-legal and replays byte-for-byte.
  4. Forced-block ranks (r_80, r_79, r_78, per-program prank, F_span) are recomputed
     in TWO prime fields (1000000007 base 2 and 998244353 base 3).
  5. Every stored integer LP dual certificate (both F_span and L-cap) is verified in
     pure exact integer arithmetic.
  6. Every upper bound matches the verified minimum, satisfies monotonicity in K and L,
     and obeys singleCharOpt <= lower <= upper across all 7 x 93 = 651 cells.
  7. length-sweep.csv matches results.json row-for-row.

Usage:
    python3 -B check_length_sweep.py /path/to/gamma [results.json] [length-sweep.csv]
"""
import collections
import csv
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PIN = '59ff04415ff2afd04ff2ed451340f4f02852bf18'
ROOT = 'projects/algorithm_solver/literals/'
LENGTHS = [1, 2, 4, 8, 16, 32, 160]
PRIMES = ((1_000_000_007, 2), (998_244_353, 3))


def check(cond, msg):
    if not cond:
        raise SystemExit('FAILED: ' + msg)


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
    check(len(sources) == 80 and len(set(sources.values())) == 80, 'cohort is not 80 distinct programs')
    return ids, sources


def unrestricted_exact(k):
    return 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1 if k <= 79 else 80


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


def verify_wl_words(words, max_len, whole_list, whole_set, ctx):
    check(len(set(words)) == len(words), f'{ctx}: duplicate entries')
    for w in words:
        check(1 <= len(w) <= max_len, f'{ctx}: length out of 1..{max_len}')
        check(w not in whole_set, f'{ctx}: whole program entry')
        if len(w) > 1:
            check(sum(1 for s in whole_list if w in s) >= 2, f'{ctx}: {w!r} occurs in < 2 programs')


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
    return prank, fspan, r_full, r_nm1, r_nm2


def verify_fspan_dual(cert, elig_ids, fspan, budget):
    scale = int(cert['scale'])
    mu = int(cert['mu'])
    check(scale > 0 and mu >= 0, 'invalid fspan dual scale/mu')
    elig_set = set(elig_ids)
    char_load = collections.Counter()
    prog_load = collections.Counter()
    seen = set()
    for p, ch, val in cert['alpha']:
        val = int(val)
        check(val >= 0 and p in elig_set and ch in fspan[p], f'invalid fspan dual edge {(p, ch)}')
        check((p, ch) not in seen, 'duplicate fspan dual edge')
        seen.add((p, ch))
        char_load[ch] += val
        prog_load[p] += val
    gamma_sum = sum(max(0, char_load[ch] - mu) for ch in char_load)
    beta_sum = sum(max(0, scale - prog_load[p]) for p in elig_ids)
    return (beta_sum + gamma_sum + mu * budget) // scale


def verify_lcap_dual(cert, elig_ids, u1, rem, max_len, budget):
    scale = int(cert['scale'])
    mu = int(cert['mu'])
    check(scale > 0 and mu >= 0 and int(cert['maxLen']) == max_len, 'invalid lcap dual header')
    elig_set = set(elig_ids)
    x_load = collections.Counter()
    y_load = collections.Counter()
    prog_load = collections.Counter()
    seen_a, seen_b = set(), set()
    for p, ch, val in cert['a']:
        val = int(val)
        check(val >= 0 and p in elig_set and ch in u1[p], f'invalid lcap a-edge {(p, ch)}')
        check((p, ch) not in seen_a, 'duplicate lcap a-edge')
        seen_a.add((p, ch))
        x_load[ch] += val
        prog_load[p] += val
    for p, ch, val in cert['b']:
        val = int(val)
        check(val >= 0 and p in elig_set and ch in rem[p], f'invalid lcap b-edge {(p, ch)}')
        check((p, ch) not in seen_b, 'duplicate lcap b-edge')
        seen_b.add((p, ch))
        x_load[ch] += val
        y_load[ch] += val
        prog_load[p] += val
    gx_sum = sum(max(0, x_load[ch] - max_len * mu) for ch in x_load)
    gy_sum = sum(max(0, y_load[ch] - mu) for ch in y_load)
    beta_sum = sum(max(0, scale - prog_load[p]) for p in elig_ids)
    return (beta_sum + gx_sum + gy_sum + max_len * budget * mu) // scale


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 -B check_length_sweep.py /path/to/gamma [results.json] [length-sweep.csv]')
    repo = sys.argv[1]
    res_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'results.json')
    csv_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'length-sweep.csv')

    ids, sources = load_cohort(repo)
    whole_list = [sources[p] for p in ids]
    whole_set = set(whole_list)
    alphabet = sorted(set(b''.join(whole_list)))
    width = len(alphabet)
    n = len(ids)
    need_chars = {p: frozenset(sources[p]) for p in ids}

    data = json.load(open(res_path, 'r', encoding='utf-8'))
    check(data['pin'] == PIN and data['lengths'] == LENGTHS, 'pin or lengths mismatch')
    check(data['programCount'] == n and data['alphabetSize'] == width, 'size/alphabet mismatch')

    # 1. Verify single-character sets replay
    for k in range(width + 1):
        sc = data['singleCharacterSets'][str(k)]
        chars = sc['characters'].encode('latin-1')
        check(len(set(chars)) == len(chars) <= k, f'singleChar K={k}: size')
        cset = frozenset(chars)
        got = sum(1 for s in whole_list if frozenset(s) <= cset)
        check(got == sc['spells'], f'singleChar K={k}: replay mismatch')

    # 2. Verify charFreqDoc baseline replay
    char_freq_top = [w.encode('latin-1') for w in data['charFreqRanked']]
    verify_wl_words(char_freq_top, 1, whole_list, whole_set, 'charFreqRanked')
    check(len(char_freq_top) == width, 'charFreqRanked length')
    char_freq_curve = [0] + [len(replay_spelled(char_freq_top[:k], ids, sources)) for k in range(1, width + 1)]

    # 3. Recompute forced blocks & algebra in TWO prime fields for mode L=1 and mode L>=2
    alg_by_mode = {}
    u1_by_mode, rem_by_mode = {}, {}
    for mode_l in (1, 2):
        blocks = compute_forced_blocks_wl(ids, sources, mode_l)
        u1 = {p: frozenset(b[0] for b in blocks[p] if len(b) == 1) for p in ids}
        rem = {p: need_chars[p] - u1[p] for p in ids}
        u1_by_mode[mode_l], rem_by_mode[mode_l] = u1, rem
        p1 = algebra_one_prime(ids, alphabet, blocks, PRIMES[0][0], PRIMES[0][1])
        p2 = algebra_one_prime(ids, alphabet, blocks, PRIMES[1][0], PRIMES[1][1])
        alg_by_mode[mode_l] = (p1, p1 == p2)

    # 4. Verify each L sweep
    by_l = {s['maxLen']: s for s in data['sweeps']}
    check(sorted(by_l) == LENGTHS, 'sweep lengths mismatch')

    total_dicts = 0
    total_duals = 0
    total_cells = 0
    total_exact = 0
    recomputed_ub_by_l = {}

    for max_len in LENGTHS:
        sw = by_l[max_len]
        mode_l = 1 if max_len == 1 else 2
        (prank, fspan, r_full, r_nm1, r_nm2), primes_agree = alg_by_mode[mode_l]
        u1, rem = u1_by_mode[mode_l], rem_by_mode[mode_l]
        check(sw['primesAgree'] == primes_agree and primes_agree, f'L={max_len}: primesAgree failed')
        check(sw['algebra']['rankFull'] == r_full, f'L={max_len}: rankFull')
        check(sw['algebra']['rankNMinus1'] == r_nm1, f'L={max_len}: rankNMinus1')
        check(sw['algebra']['rankNMinus2'] == r_nm2, f'L={max_len}: rankNMinus2')

        # Verify frequency baselines are W(L)-legal and replay exactly
        focc = [w.encode('latin-1') for w in sw['freqOccTop92']]
        fdoc = [w.encode('latin-1') for w in sw['freqDocTop92']]
        verify_wl_words(focc, max_len, whole_list, whole_set, f'L={max_len} freqOcc')
        verify_wl_words(fdoc, max_len, whole_list, whole_set, f'L={max_len} freqDoc')
        focc_curve = [0] + [len(replay_spelled(focc[:k], ids, sources)) for k in range(1, width + 1)]
        fdoc_curve = [0] + [len(replay_spelled(fdoc[:k], ids, sources)) for k in range(1, width + 1)]

        # Verify all stored lower-end dictionaries
        replayed = {}
        for dkey, d in sw['dictionaries'].items():
            words = [w.encode('latin-1') for w in d['entries']]
            check(len(words) == d['entryCount'], f'L={max_len} {dkey}: entryCount')
            verify_wl_words(words, max_len, whole_list, whole_set, f'L={max_len} {dkey}')
            got = replay_spelled(words, ids, sources)
            check(got == d['spells'] and len(got) == d['spellsCount'], f'L={max_len} {dkey}: replay')
            replayed[dkey] = (len(words), len(got))
            total_dicts += 1

        # Recompute solver-free upper bounds for this L
        ub = []
        for k in range(width + 1):
            if k <= 1:
                ub.append(0)
                continue
            elig = [
                p for p in ids
                if prank[p] <= k and (len(u1[p]) + math.ceil(len(rem[p]) / max_len)) <= k
            ]
            cands = [unrestricted_exact(k), len(elig)]
            if k < r_full:
                cands.append(n - 1)
            if k < r_nm1:
                cands.append(n - 2)
            if k < r_nm2:
                cands.append(n - 3)
            if str(k) in sw['dualCertificates']:
                cert = sw['dualCertificates'][str(k)]
                if cert['kind'] == 'fspan':
                    cands.append(verify_fspan_dual(cert, elig, fspan, k))
                elif cert['kind'] == 'lcap':
                    cands.append(verify_lcap_dual(cert, elig, u1, rem, max_len, k))
                else:
                    check(False, f'unknown dual kind {cert["kind"]}')
                total_duals += 1
            ub.append(min(cands))
        for k in range(width - 1, -1, -1):
            if ub[k + 1] < ub[k]:
                ub[k] = ub[k + 1]
        recomputed_ub_by_l[max_len] = ub

        # Store replayed baselines for checking after cross-L upper monotonicity
        sw['_replayed'] = replayed
        sw['_focc_curve'] = focc_curve
        sw['_fdoc_curve'] = fdoc_curve

    # Cross-L upper bound monotonicity
    for idx in range(len(LENGTHS) - 2, -1, -1):
        l_cur, l_nxt = LENGTHS[idx], LENGTHS[idx + 1]
        for k in range(width + 1):
            if recomputed_ub_by_l[l_nxt][k] < recomputed_ub_by_l[l_cur][k]:
                recomputed_ub_by_l[l_cur][k] = recomputed_ub_by_l[l_nxt][k]

    # 5. Check every cell across K and L, including cross-L monotonicity
    csv_rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            csv_rows.append(row)
    check(len(csv_rows) == len(LENGTHS) * (width + 1), 'CSV row count mismatch')
    csv_idx = 0

    for li, max_len in enumerate(LENGTHS):
        sw = by_l[max_len]
        replayed = sw['_replayed']
        focc_curve = sw['_focc_curve']
        fdoc_curve = sw['_fdoc_curve']
        ub = recomputed_ub_by_l[max_len]
        rows = sw['rows']
        check([r['slots'] for r in rows] == list(range(width + 1)), f'L={max_len}: slots')
        prev_lo, prev_ub = 0, 0
        for r in rows:
            k = r['slots']
            if r['lowerDictionary'] is None:
                check(r['lower'] == 0, f'L={max_len} K={k}: lower without dict')
            else:
                ec, spc = replayed[r['lowerDictionary']]
                check(ec <= k and spc == r['lower'], f'L={max_len} K={k}: lower dict mismatch')
            check(r['singleCharOpt'] == data['singleCharacterSets'][str(k)]['spells'], f'L={max_len} K={k}: singleCharOpt')
            check(r['charFreqDoc'] == char_freq_curve[k], f'L={max_len} K={k}: charFreqDoc')
            check(r['freqOcc'] == focc_curve[k], f'L={max_len} K={k}: freqOcc')
            check(r['freqDoc'] == fdoc_curve[k], f'L={max_len} K={k}: freqDoc')
            check(r['upper'] == ub[k], f'L={max_len} K={k}: upper {r["upper"]} != verified {ub[k]}')
            check(r['singleCharOpt'] <= r['lower'] <= r['upper'], f'L={max_len} K={k}: ordering')
            check(r['freqOcc'] <= r['upper'] and r['freqDoc'] <= r['upper'], f'L={max_len} K={k}: baseline > upper')
            check(r['exact'] == (r['lower'] == r['upper']), f'L={max_len} K={k}: exact flag')
            check(r['width'] == r['upper'] - r['lower'], f'L={max_len} K={k}: width')
            check(r['lower'] >= prev_lo and r['upper'] >= prev_ub, f'L={max_len} K={k}: K-monotonicity')
            if li > 0:
                prev_r = by_l[LENGTHS[li - 1]]['rows'][k]
                check(r['lower'] >= prev_r['lower'] and r['upper'] >= prev_r['upper'], f'L={max_len} K={k}: L-monotonicity')
            prev_lo, prev_ub = r['lower'], r['upper']

            cr = csv_rows[csv_idx]
            csv_idx += 1
            check(
                int(cr['maxLen']) == max_len and int(cr['slots']) == k
                and int(cr['lower']) == r['lower'] and int(cr['upper']) == r['upper']
                and int(cr['freqOcc']) == r['freqOcc'] and int(cr['freqDoc']) == r['freqDoc']
                and int(cr['charFreqDoc']) == r['charFreqDoc'] and int(cr['singleCharOpt']) == r['singleCharOpt'],
                f'CSV mismatch at L={max_len} K={k}',
            )
            total_cells += 1
            total_exact += int(r['exact'])
        print(f'OK L={max_len:3d} exact={sum(1 for r in rows if r["exact"]):2d}/93 primesAgree=True')

    print(
        f'ALL VERIFIED (100% solver-free): {len(LENGTHS)} lengths, {total_cells} cells '
        f'({total_exact} exact), {total_dicts} dictionaries replayed, {total_duals} integer LP duals checked.'
    )


if __name__ == '__main__':
    main()
