#!/usr/bin/env python3
"""Pre-registered unseen-program K x L transfer test on frozen disjoint -a / -b cohorts.

Reads the frozen disjoint cohorts from ../witness-scaling-v1/cohorts.json for:
  J-80-a -> J-80-b, P-80-a -> P-80-b, J-160-a -> J-160-b, P-160-a -> P-160-b.

Trains and freezes dictionaries EXCLUSIVELY on each -a cohort across L in [1, 2, 4, 8, 16, 32, 160]
and K in 0..|Sigma_a| for:
  - charOpt (exact single-char MILP on -a)
  - charFreqDoc (top-K single chars by doc freq on -a)
  - freqOcc / freqDoc (top-K W(L)-legal entries by occurrence / doc freq on -a)
  - jointBest (best -a W(L)-legal dictionary across charOpt, 4-start greedy DP, rare-char compression)
  - greedyDP (best pure greedy DP W(L)-legal dictionary on -a without charOpt fallback)

Scores every frozen dictionary byte-for-byte on both -a (train) and -b (unseen holdout), records
exact stored dictionary bytes, and extracts the actual multi-character fragments used whenever an
unseen -b program is spelled by jointBest or greedyDP but not by charOpt.

Usage:
    python3 -B run_unseen_transfer.py [../witness-scaling-v1/cohorts.json] [transfer-results.json] [unseen-transfer.csv]
"""
import collections
import csv
import hashlib
import json
import os
import random
import sys
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_COHORTS = os.path.join(HERE, '..', 'witness-scaling-v1', 'cohorts.json')
PAIRS = [
    ('J-80', 'J-80-a', 'J-80-b'),
    ('P-80', 'P-80-a', 'P-80-b'),
    ('J-160', 'J-160-a', 'J-160-b'),
    ('P-160', 'P-160-a', 'P-160-b'),
]
LENGTHS = [1, 2, 4, 8, 16, 32, 160]


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


def extract_parse_fragments(words, s):
    """Return one valid parse of s using words (preferring fewest pieces), listing multi-char pieces used."""
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    n = len(s)
    inf = 10**9
    dist = [inf] * (n + 1)
    prev = [None] * (n + 1)
    dist[0] = 0
    for i in range(n):
        di = dist[i]
        if di == inf:
            continue
        for w in by_first.get(s[i], ()):
            j = i + len(w)
            if j <= n and s.startswith(w, i) and di + 1 < dist[j]:
                dist[j] = di + 1
                prev[j] = (i, w)
    if dist[n] == inf:
        return None
    used = []
    j = n
    while j > 0:
        i, w = prev[j]
        if len(w) > 1:
            used.append(w.decode('ascii'))
        j = i
    return sorted(set(used))


def compute_shared_len_and_counts(ids, sources, max_cap=160):
    whole_set = set(sources.values())
    shared_len = {p: [0] * len(sources[p]) for p in ids}
    doc_freq = {}
    total_occ = {}
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
    rare = [ch for ch in chars if len(char_occ[ch]) <= 12]
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
    for sub, _ in cand_subs.most_common(64):
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


def evaluate_pair(pair_id, tr_cohort, te_cohort):
    t0 = time.monotonic()
    tr_ids = [p['id'] for p in tr_cohort['programs']]
    te_ids = [p['id'] for p in te_cohort['programs']]
    tr_src = {p['id']: p['text'].encode('ascii') for p in tr_cohort['programs']}
    te_src = {p['id']: p['text'].encode('ascii') for p in te_cohort['programs']}
    tr_whole_list = [tr_src[p] for p in tr_ids]
    tr_whole_set = set(tr_whole_list)
    alphabet = sorted(set(b''.join(tr_whole_list)))
    width = len(alphabet)
    need_tr = {p: frozenset(tr_src[p]) for p in tr_ids}
    need_te = {p: frozenset(te_src[p]) for p in te_ids}

    # 1. Single-char MILP on -a (Arm a)
    singles_milp = solve_char_cover_milp(tr_ids, need_tr, alphabet)
    char_opt_sets = {}
    char_opt_tr = []
    char_opt_te = []
    char_opt_te_ids = []
    for k in range(width + 1):
        opt, chosen = singles_milp[k]
        cset = frozenset(chosen)
        tr_sp = [p for p in tr_ids if need_tr[p] <= cset]
        te_sp = [p for p in te_ids if need_te[p] <= cset]
        assert len(tr_sp) == opt
        char_opt_sets[str(k)] = {
            'characters': bytes(chosen).decode('ascii'),
            'trainSpelled': len(tr_sp),
            'testSpelled': len(te_sp),
            'dictBytes': len(chosen),
        }
        char_opt_tr.append(len(tr_sp))
        char_opt_te.append(len(te_sp))
        char_opt_te_ids.append(set(te_sp))

    # 2. Shared lengths & counts on -a ONLY
    shared_len, doc_freq, total_occ = compute_shared_len_and_counts(tr_ids, tr_src, max(LENGTHS))

    # Single-char doc-freq baseline on -a
    char_freq_top = sorted([bytes([c]) for c in alphabet], key=lambda w: (-doc_freq[w], -total_occ[w], w))
    char_freq_tr = [0]
    char_freq_te = [0]
    for k in range(1, width + 1):
        cset = frozenset(w[0] for w in char_freq_top[:k])
        char_freq_tr.append(sum(1 for p in tr_ids if need_tr[p] <= cset))
        char_freq_te.append(sum(1 for p in te_ids if need_te[p] <= cset))

    prev_joint_dicts = {}  # k -> (tr_cnt, wset)
    sweeps = []

    for max_len in LENGTHS:
        wl_vocab = [w for w in doc_freq if len(w) <= max_len]
        ranked_occ = sorted(wl_vocab, key=lambda w: (-total_occ[w], -doc_freq[w], len(w), w))[:width]
        ranked_doc = sorted(wl_vocab, key=lambda w: (-doc_freq[w], -total_occ[w], -len(w), w))[:width]
        assert is_legal_wl(ranked_occ, max_len, tr_whole_list, tr_whole_set)
        assert is_legal_wl(ranked_doc, max_len, tr_whole_list, tr_whole_set)

        freq_occ_tr = [0] + [len(replay_spelled(ranked_occ[:k], tr_ids, tr_src)) for k in range(1, width + 1)]
        freq_occ_te = [0] + [len(replay_spelled(ranked_occ[:k], te_ids, te_src)) for k in range(1, width + 1)]
        freq_occ_bytes = [0] + [sum(len(w) for w in ranked_occ[:k]) for k in range(1, width + 1)]

        freq_doc_tr = [0] + [len(replay_spelled(ranked_doc[:k], tr_ids, tr_src)) for k in range(1, width + 1)]
        freq_doc_te = [0] + [len(replay_spelled(ranked_doc[:k], te_ids, te_src)) for k in range(1, width + 1)]
        freq_doc_bytes = [0] + [sum(len(w) for w in ranked_doc[:k]) for k in range(1, width + 1)]

        best_joint = {}   # k -> (tr_cnt, -dict_bytes, label, wset, tr_sp)
        best_greedy = {}  # k -> (tr_cnt, -dict_bytes, label, wset, tr_sp)

        def offer(bucket, words, label):
            wset = frozenset(words)
            if not wset or len(wset) > width:
                return
            if not is_legal_wl(wset, max_len, tr_whole_list, tr_whole_set):
                return
            tr_sp = replay_spelled(wset, tr_ids, tr_src)
            k = len(wset)
            dbytes = sum(len(w) for w in wset)
            key = (len(tr_sp), -dbytes)
            cur = bucket.get(k)
            if cur is None or key > (cur[0], cur[1]):
                bucket[k] = (len(tr_sp), -dbytes, label, wset, tr_sp)

        # Offer charOpt to jointBest (and to greedyDP only at L=1)
        for k in range(1, width + 1):
            chosen = char_opt_sets[str(k)]['characters'].encode('ascii')
            cwords = [bytes([c]) for c in chosen]
            offer(best_joint, cwords, 'single characters')
            if max_len == 1:
                offer(best_greedy, cwords, 'single characters')

        # Inherit from smaller L into jointBest
        for k, prev_wset in prev_joint_dicts.items():
            offer(best_joint, prev_wset, f'inherited from L<{max_len}')

        if max_len >= 2:
            configs = [
                (0.0, 0.001, 0.0, None, 'greedy DP, single preferred'),
                (0.001, 0.0, 0.0, None, 'greedy DP, multi preferred'),
                (0.001, 0.0, 1e-4, None, 'greedy DP, longer multi preferred'),
                (0.001, 0.0, 0.0, f'{pair_id}/L{max_len}/s0', 'greedy DP, multi tie seed 0'),
            ]
            for bias_s, bias_m, len_b, seed, label in configs:
                rng = random.Random(seed) if seed is not None else None
                have = set()
                group = set()
                by_first = collections.defaultdict(list)
                while len(group) < len(tr_ids) and len(have) < width:
                    options = []
                    for p in tr_ids:
                        if p in group:
                            continue
                        new = parse_cost_dp(
                            tr_src[p], shared_len[p], max_len, by_first, have, bias_s, bias_m, len_b, tr_whole_set
                        )
                        tie = rng.random() if rng else 0.0
                        options.append((len(new), tie, p, new))
                    _, _, p, new = min(options)
                    if any(w in tr_whole_set or len(w) > max_len for w in new):
                        new = {w for w in new if w not in tr_whole_set and len(w) <= max_len} | {
                            bytes([c]) for w in new if (w in tr_whole_set or len(w) > max_len) for c in w
                        }
                    for w in new:
                        have.add(w)
                        by_first[w[0]].append(w)
                    group.add(p)
                    if len(have) <= width:
                        offer(best_joint, have, label)
                        offer(best_greedy, have, label)

            # Rare-character cluster compression on top 35 budgets
            tested = set()
            for k in range(max(1, width - 35), width + 1):
                chosen = frozenset(char_opt_sets[str(k)]['characters'].encode('ascii'))
                sub_ids = tuple(p for p in tr_ids if need_tr[p] <= chosen)
                if sub_ids and sub_ids not in tested:
                    tested.add(sub_ids)
                    comp = compress_rare_char_clusters(list(sub_ids), tr_src, shared_len, max_len, tr_whole_list, tr_whole_set)
                    if comp is not None:
                        offer(best_joint, comp, 'rare-char cluster compression')
                uncov = [p for p in tr_ids if not (need_tr[p] <= chosen)]
                uncov.sort(key=lambda p: (len(need_tr[p] - chosen), p))
                if uncov:
                    sub_plus = tuple(sorted(set(sub_ids) | {uncov[0]}))
                    if sub_plus not in tested:
                        tested.add(sub_plus)
                        comp = compress_rare_char_clusters(list(sub_plus), tr_src, shared_len, max_len, tr_whole_list, tr_whole_set)
                        if comp is not None:
                            offer(best_joint, comp, 'rare-char cluster compression (+1)')

        # Freeze monotone-in-K dictionaries selected strictly on -a train performance, then score on unseen -b
        def freeze_arm(bucket, prefix):
            stored = {}
            rows_arm = []
            cur_tr = -1
            cur_bytes = 0
            cur_key = None
            cur_wset = frozenset()
            cur_te_sp = []
            for k in range(width + 1):
                if k == 0:
                    rows_arm.append((0, 0, 0, 0, None, []))
                    continue
                cand = bucket.get(k)
                if cand is not None and (cand[0] > cur_tr or (cand[0] == cur_tr and -cand[1] < cur_bytes)):
                    tr_cnt, neg_b, label, wset, tr_sp = cand
                    te_sp = replay_spelled(wset, te_ids, te_src)
                    cur_tr = tr_cnt
                    cur_bytes = -neg_b
                    cur_wset = wset
                    cur_te_sp = te_sp
                    cur_key = f'{prefix}_L{max_len}_K{k}'
                    stored[cur_key] = {
                        'entryCount': len(wset),
                        'multiCharacterEntries': sum(1 for w in wset if len(w) > 1),
                        'dictBytes': cur_bytes,
                        'source': label,
                        'entries': sorted(w.decode('ascii') for w in wset),
                        'trainSpelled': tr_cnt,
                        'testSpelled': len(te_sp),
                    }
                rows_arm.append((
                    max(0, cur_tr),
                    len(cur_te_sp),
                    cur_bytes,
                    sum(1 for w in cur_wset if len(w) > 1),
                    cur_key,
                    cur_te_sp,
                ))
            return stored, rows_arm

        joint_dicts, joint_arm = freeze_arm(best_joint, 'joint')
        greedy_dicts, greedy_arm = freeze_arm(best_greedy, 'greedy')

        # Collect next inherited dicts (multi-char ones that won on -a)
        next_prev = {}
        for k, val in best_joint.items():
            next_prev[k] = val[3]
        prev_joint_dicts = next_prev

        # Extract concrete fragment attribution whenever jointBest or greedyDP gains unseen -b programs over charOpt
        unseen_gains = []
        rows = []
        for k in range(width + 1):
            j_tr, j_te, j_bytes, j_multi, j_key, j_te_sp = joint_arm[k]
            g_tr, g_te, g_bytes, g_multi, g_key, g_te_sp = greedy_arm[k]
            base_te_set = char_opt_te_ids[k]

            if j_te > char_opt_te[k] and j_key is not None:
                gained = sorted(set(j_te_sp) - base_te_set)
                wset = [w.encode('ascii') for w in joint_dicts[j_key]['entries']]
                frag_map = {p: extract_parse_fragments(wset, te_src[p]) for p in gained}
                unseen_gains.append({
                    'arm': 'jointBest',
                    'slots': k,
                    'netTestLift': j_te - char_opt_te[k],
                    'gainedTestPrograms': gained,
                    'fragmentsUsed': frag_map,
                })
            if g_te > char_opt_te[k] and g_key is not None:
                gained = sorted(set(g_te_sp) - base_te_set)
                wset = [w.encode('ascii') for w in greedy_dicts[g_key]['entries']]
                frag_map = {p: extract_parse_fragments(wset, te_src[p]) for p in gained}
                unseen_gains.append({
                    'arm': 'greedyDP',
                    'slots': k,
                    'netTestLift': g_te - char_opt_te[k],
                    'gainedTestPrograms': gained,
                    'fragmentsUsed': frag_map,
                })

            rows.append({
                'pairId': pair_id,
                'maxLen': max_len,
                'slots': k,
                'charOptTrain': char_opt_tr[k],
                'charOptTest': char_opt_te[k],
                'charOptBytes': char_opt_sets[str(k)]['dictBytes'],
                'charFreqDocTrain': char_freq_tr[k],
                'charFreqDocTest': char_freq_te[k],
                'freqOccTrain': freq_occ_tr[k],
                'freqOccTest': freq_occ_te[k],
                'freqOccBytes': freq_occ_bytes[k],
                'freqDocTrain': freq_doc_tr[k],
                'freqDocTest': freq_doc_te[k],
                'freqDocBytes': freq_doc_bytes[k],
                'jointBestTrain': j_tr,
                'jointBestTest': j_te,
                'jointBestBytes': j_bytes,
                'jointBestMulti': j_multi,
                'jointBestDict': j_key,
                'greedyDPTrain': g_tr,
                'greedyDPTest': g_te,
                'greedyDPBytes': g_bytes,
                'greedyDPMulti': g_multi,
                'greedyDPDict': g_key,
            })

        sweeps.append({
            'maxLen': max_len,
            'legalVocabSize': len(wl_vocab),
            'freqOccTop': [w.decode('ascii') for w in ranked_occ],
            'freqDocTop': [w.decode('ascii') for w in ranked_doc],
            'jointDictionaries': joint_dicts,
            'greedyDictionaries': greedy_dicts,
            'unseenGains': unseen_gains,
            'rows': rows,
        })

    elapsed = round(time.monotonic() - t0, 2)
    sw160 = sweeps[-1]
    r64 = sw160['rows'][64]
    mean_j_diff = float(np.mean([r['jointBestTest'] - r['charOptTest'] for r in sw160['rows']]))
    mean_g_diff = float(np.mean([r['greedyDPTest'] - r['charOptTest'] for r in sw160['rows']]))
    peak_j_lift = max(r['jointBestTest'] - r['charOptTest'] for r in sw160['rows'])
    peak_g_lift = max(r['greedyDPTest'] - r['charOptTest'] for r in sw160['rows'])
    print(
        f'{pair_id:5s} (|Sigma_a|={width}) L=160: K64 test charOpt={r64["charOptTest"]} charFreq={r64["charFreqDocTest"]} '
        f'freqOcc={r64["freqOccTest"]} freqDoc={r64["freqDocTest"]} joint={r64["jointBestTest"]}({r64["jointBestBytes"]}B) '
        f'greedy={r64["greedyDPTest"]}({r64["greedyDPBytes"]}B) | '
        f'peakLift(joint={peak_j_lift}, greedy={peak_g_lift}) meanDiff(joint={mean_j_diff:+.2f}, greedy={mean_g_diff:+.2f}) t={elapsed}s',
        flush=True,
    )
    return {
        'pairId': pair_id,
        'trainCohort': tr_cohort['cohortId'],
        'testCohort': te_cohort['cohortId'],
        'trainSize': len(tr_ids),
        'testSize': len(te_ids),
        'trainAlphabetSize': width,
        'charFreqRanked': [w.decode('ascii') for w in char_freq_top],
        'charOptSets': char_opt_sets,
        'sweeps': sweeps,
        'seconds': elapsed,
    }


def main():
    cohorts_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COHORTS
    out_json = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'transfer-results.json')
    out_csv = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'unseen-transfer.csv')

    cohorts_sha = hashlib.sha256(open(cohorts_path, 'rb').read()).hexdigest()
    cohorts_data = json.load(open(cohorts_path, 'r', encoding='utf-8'))
    by_id = {c['cohortId']: c for c in cohorts_data['cohorts']}

    t_all = time.monotonic()
    pair_results = []
    for pair_id, tr_id, te_id in PAIRS:
        pair_results.append(evaluate_pair(pair_id, by_id[tr_id], by_id[te_id]))

    out = {
        'cohortsSha256': cohorts_sha,
        'lengths': LENGTHS,
        'totalSeconds': round(time.monotonic() - t_all, 2),
        'pairs': pair_results,
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    fieldnames = [
        'pairId', 'maxLen', 'slots',
        'charOptTrain', 'charOptTest', 'charOptBytes',
        'charFreqDocTrain', 'charFreqDocTest',
        'freqOccTrain', 'freqOccTest', 'freqOccBytes',
        'freqDocTrain', 'freqDocTest', 'freqDocBytes',
        'jointBestTrain', 'jointBestTest', 'jointBestBytes', 'jointBestMulti', 'jointBestDict',
        'greedyDPTrain', 'greedyDPTest', 'greedyDPBytes', 'greedyDPMulti', 'greedyDPDict',
    ]
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pr in pair_results:
            for sw in pr['sweeps']:
                for r in sw['rows']:
                    w.writerow({k: r[k] for k in fieldnames})

    h_json = hashlib.sha256(open(out_json, 'rb').read()).hexdigest()
    h_csv = hashlib.sha256(open(out_csv, 'rb').read()).hexdigest()
    print(f'Wrote {out_json} ({os.path.getsize(out_json):,} bytes, sha256={h_json})')
    print(f'Wrote {out_csv} ({os.path.getsize(out_csv):,} bytes, sha256={h_csv}) in {out["totalSeconds"]}s')


if __name__ == '__main__':
    main()
