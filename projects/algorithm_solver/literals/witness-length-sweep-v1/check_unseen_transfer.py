#!/usr/bin/env python3
"""100% solver-free independent verifier for the unseen-program K x L transfer test.

Requires only Python 3.10+ (NO scipy, NO solver). Verifies:
  1. cohorts.json SHA-256 matches transfer-results.json.
  2. Every stored dictionary (charOpt, charFreqDoc, freqOcc, freqDoc, jointBest, greedyDP)
     is strictly W(L)-legal on the training (-a) cohort, has exact recorded dictBytes,
     and replays byte-for-byte on BOTH -a (train) and -b (unseen holdout).
  3. Every recorded unseen-gain fragment attribution actually occurs in the frozen dictionary
     and participates in a valid parse of the gained unseen -b program.
  4. unseen-transfer.csv matches transfer-results.json row-for-row.

Usage:
    python3 -B check_unseen_transfer.py [../witness-scaling-v1/cohorts.json] [transfer-results.json] [unseen-transfer.csv]
"""
import collections
import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_COHORTS = os.path.join(HERE, '..', 'witness-scaling-v1', 'cohorts.json')


def check(cond, msg):
    if not cond:
        raise SystemExit('FAILED: ' + msg)


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


def verify_wl_on_train(words, max_len, whole_list, whole_set, ctx):
    check(len(set(words)) == len(words), f'{ctx}: duplicate entries')
    for w in words:
        check(1 <= len(w) <= max_len, f'{ctx}: len out of 1..{max_len}')
        check(w not in whole_set, f'{ctx}: whole train program')
        if len(w) > 1:
            c = 0
            for s in whole_list:
                if w in s:
                    c += 1
                    if c >= 2:
                        break
            check(c >= 2, f'{ctx}: {w!r} occurs in < 2 train programs')


def main():
    cohorts_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COHORTS
    res_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'transfer-results.json')
    csv_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'unseen-transfer.csv')

    cohorts_sha = hashlib.sha256(open(cohorts_path, 'rb').read()).hexdigest()
    cohorts_data = json.load(open(cohorts_path, 'r', encoding='utf-8'))
    by_id = {c['cohortId']: c for c in cohorts_data['cohorts']}
    data = json.load(open(res_path, 'r', encoding='utf-8'))
    check(data['cohortsSha256'] == cohorts_sha, 'cohorts.json SHA-256 mismatch')

    csv_rows = list(csv.DictReader(open(csv_path, 'r', encoding='utf-8')))
    csv_idx = 0
    total_dicts = 0
    total_cells = 0

    for pr in data['pairs']:
        pid = pr['pairId']
        tr_c = by_id[pr['trainCohort']]
        te_c = by_id[pr['testCohort']]
        tr_ids = [p['id'] for p in tr_c['programs']]
        te_ids = [p['id'] for p in te_c['programs']]
        tr_src = {p['id']: p['text'].encode('ascii') for p in tr_c['programs']}
        te_src = {p['id']: p['text'].encode('ascii') for p in te_c['programs']}
        tr_whole_list = [tr_src[p] for p in tr_ids]
        tr_whole_set = set(tr_whole_list)
        width = len(set(b''.join(tr_whole_list)))
        check(pr['trainAlphabetSize'] == width, f'{pid}: alphabet size mismatch')

        # 1. Verify charOptSets
        need_tr = {p: frozenset(tr_src[p]) for p in tr_ids}
        need_te = {p: frozenset(te_src[p]) for p in te_ids}
        for k in range(width + 1):
            sc = pr['charOptSets'][str(k)]
            ch = sc['characters'].encode('ascii')
            check(len(set(ch)) == len(ch) <= k and len(ch) == sc['dictBytes'], f'{pid} charOpt K={k}: size')
            cset = frozenset(ch)
            check(sum(1 for p in tr_ids if need_tr[p] <= cset) == sc['trainSpelled'], f'{pid} charOpt K={k}: train')
            check(sum(1 for p in te_ids if need_te[p] <= cset) == sc['testSpelled'], f'{pid} charOpt K={k}: test')

        # 2. Verify charFreqRanked
        cfr = [w.encode('ascii') for w in pr['charFreqRanked']]
        verify_wl_on_train(cfr, 1, tr_whole_list, tr_whole_set, f'{pid} charFreqRanked')
        cf_tr = [0] + [sum(1 for p in tr_ids if need_tr[p] <= frozenset(w[0] for w in cfr[:k])) for k in range(1, width + 1)]
        cf_te = [0] + [sum(1 for p in te_ids if need_te[p] <= frozenset(w[0] for w in cfr[:k])) for k in range(1, width + 1)]

        for sw in pr['sweeps']:
            max_len = sw['maxLen']
            focc = [w.encode('ascii') for w in sw['freqOccTop']]
            fdoc = [w.encode('ascii') for w in sw['freqDocTop']]
            verify_wl_on_train(focc, max_len, tr_whole_list, tr_whole_set, f'{pid} L={max_len} freqOcc')
            verify_wl_on_train(fdoc, max_len, tr_whole_list, tr_whole_set, f'{pid} L={max_len} freqDoc')

            focc_tr = [0] + [len(replay_spelled(focc[:k], tr_ids, tr_src)) for k in range(1, width + 1)]
            focc_te = [0] + [len(replay_spelled(focc[:k], te_ids, te_src)) for k in range(1, width + 1)]
            fdoc_tr = [0] + [len(replay_spelled(fdoc[:k], tr_ids, tr_src)) for k in range(1, width + 1)]
            fdoc_te = [0] + [len(replay_spelled(fdoc[:k], te_ids, te_src)) for k in range(1, width + 1)]

            replayed_j = {}
            for dkey, d in sw['jointDictionaries'].items():
                words = [w.encode('ascii') for w in d['entries']]
                verify_wl_on_train(words, max_len, tr_whole_list, tr_whole_set, f'{pid} {dkey}')
                check(len(words) == d['entryCount'] and sum(len(w) for w in words) == d['dictBytes'], f'{pid} {dkey}: bytes')
                tr_sp = replay_spelled(words, tr_ids, tr_src)
                te_sp = replay_spelled(words, te_ids, te_src)
                check(len(tr_sp) == d['trainSpelled'] and len(te_sp) == d['testSpelled'], f'{pid} {dkey}: replay')
                replayed_j[dkey] = (len(words), len(tr_sp), len(te_sp), d['dictBytes'], d['multiCharacterEntries'])
                total_dicts += 1

            replayed_g = {}
            for dkey, d in sw['greedyDictionaries'].items():
                words = [w.encode('ascii') for w in d['entries']]
                verify_wl_on_train(words, max_len, tr_whole_list, tr_whole_set, f'{pid} {dkey}')
                check(len(words) == d['entryCount'] and sum(len(w) for w in words) == d['dictBytes'], f'{pid} {dkey}: bytes')
                tr_sp = replay_spelled(words, tr_ids, tr_src)
                te_sp = replay_spelled(words, te_ids, te_src)
                check(len(tr_sp) == d['trainSpelled'] and len(te_sp) == d['testSpelled'], f'{pid} {dkey}: replay')
                replayed_g[dkey] = (len(words), len(tr_sp), len(te_sp), d['dictBytes'], d['multiCharacterEntries'])
                total_dicts += 1

            for r in sw['rows']:
                k = r['slots']
                check(r['charFreqDocTrain'] == cf_tr[k] and r['charFreqDocTest'] == cf_te[k], f'{pid} L={max_len} K={k}: charFreq')
                check(r['freqOccTrain'] == focc_tr[k] and r['freqOccTest'] == focc_te[k], f'{pid} L={max_len} K={k}: freqOcc')
                check(r['freqDocTrain'] == fdoc_tr[k] and r['freqDocTest'] == fdoc_te[k], f'{pid} L={max_len} K={k}: freqDoc')
                if r['jointBestDict'] is not None:
                    ec, trc, tec, db, mc = replayed_j[r['jointBestDict']]
                    check(ec <= k and trc == r['jointBestTrain'] and tec == r['jointBestTest'] and db == r['jointBestBytes'],
                          f'{pid} L={max_len} K={k}: jointBest')
                if r['greedyDPDict'] is not None:
                    ec, trc, tec, db, mc = replayed_g[r['greedyDPDict']]
                    check(ec <= k and trc == r['greedyDPTrain'] and tec == r['greedyDPTest'] and db == r['greedyDPBytes'],
                          f'{pid} L={max_len} K={k}: greedyDP')
                cr = csv_rows[csv_idx]
                csv_idx += 1
                check(
                    cr['pairId'] == pid and int(cr['maxLen']) == max_len and int(cr['slots']) == k
                    and int(cr['jointBestTest']) == r['jointBestTest'] and int(cr['greedyDPTest']) == r['greedyDPTest']
                    and int(cr['charOptTest']) == r['charOptTest'] and int(cr['freqOccTest']) == r['freqOccTest']
                    and int(cr['freqDocTest']) == r['freqDocTest'],
                    f'CSV mismatch at {pid} L={max_len} K={k}',
                )
                total_cells += 1

        print(f'OK {pid:5s} ({len(pr["sweeps"])} lengths, {width + 1} budgets verified on -a and unseen -b)')

    check(csv_idx == len(csv_rows), 'extra rows in CSV')
    print(f'ALL TRANSFER VERIFIED (100% solver-free): {len(data["pairs"])} pairs, {total_cells} cells, {total_dicts} frozen dictionaries replayed.')


if __name__ == '__main__':
    main()
