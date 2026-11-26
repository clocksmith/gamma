#!/usr/bin/env python3
"""Supplementary checks for the unseen-program transfer test. Post hoc, written 2026-11-26.

    python3 -B recheck_unseen_transfer.py            # about a minute; Python 3 only; writes nothing
    python3 -B recheck_unseen_transfer.py --quick    # skips the frozen checker (40 s of the minute)

`check_unseen_transfer.py` is frozen (SHA256SUMS-TRANSFER-FROZEN) and is not edited. A review found
that it does less than its docstring and RESULTS.md say:

  - it never replays the recorded unseen-gain attributions (item 3 of its docstring);
  - it compares each row's charOptTrain and charOptTest only with the CSV written by the same run,
    never with the single-character sets it has just replayed, so the training lift quoted in
    RESULTS.md ("+1 to +4") rested on a number nothing checked;
  - it compares five of the 24 CSV columns with the JSON;
  - a row that names no dictionary is not checked at all, and the count of multi-character entries
    in a row is never recounted.

This script runs the frozen checker, then does those checks, then recomputes the sentences
of RESULTS.md that depend on them from the values it has verified. The expected values below are
typed from RESULTS.md: they are the claims under test. Exit status 0 only if everything agrees.
"""
import collections
import csv
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from check_unseen_transfer import replay_spelled  # noqa: E402  (the frozen replay, imported unchanged)

SUMS = ('SHA256SUMS-FROZEN', 'SHA256SUMS-TRANSFER-FROZEN', 'SHA256SUMS-RESULTS')
ARMS = (('jointBest', 'jointDictionaries'), ('greedyDP', 'greedyDictionaries'))
FAILED = []


def check(cond, message):
    if not cond:
        FAILED.append(message)
    return cond


def spellable(words, s):
    """forward[i]: s[:i] can be spelled; backward[i]: s[i:] can be spelled."""
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    n = len(s)
    forward = [False] * (n + 1)
    forward[0] = True
    for i in range(n):
        if forward[i]:
            for w in by_first.get(s[i], ()):
                if s.startswith(w, i):
                    forward[i + len(w)] = True
    backward = [False] * (n + 1)
    backward[n] = True
    for i in range(n - 1, -1, -1):
        backward[i] = any(s.startswith(w, i) and backward[i + len(w)] for w in by_first.get(s[i], ()))
    return forward, backward


def in_a_valid_parse(w, words, s):
    """Is there a way to spell all of s with `words` that uses w at least once?"""
    forward, backward = spellable(words, s)
    i = s.find(w)
    while i >= 0:
        if forward[i] and backward[i + len(w)]:
            return True
        i = s.find(w, i + 1)
    return False


def main():
    quick = '--quick' in sys.argv
    for name in SUMS:
        for line in open(os.path.join(HERE, name), encoding='utf-8').read().splitlines():
            digest, rel = line.split(None, 1)
            got = hashlib.sha256(open(os.path.join(HERE, rel.strip()), 'rb').read()).hexdigest()
            check(got == digest, f'{rel.strip()} does not match {name}')
    if FAILED:
        print('\n'.join('FAILED: ' + f for f in FAILED))
        return 1
    print('frozen and result files match their three checksum lists')
    if not quick:
        done = subprocess.run([sys.executable, '-B', 'check_unseen_transfer.py'], cwd=HERE, capture_output=True, text=True)
        check(done.returncode == 0 and 'ALL TRANSFER VERIFIED' in done.stdout, 'the frozen checker failed: ' + done.stdout[-200:])
        print('frozen checker:', done.stdout.strip().splitlines()[-1])

    cohorts = json.load(open(os.path.join(HERE, '..', 'witness-scaling-v1', 'cohorts.json'), encoding='utf-8'))
    by_id = {c['cohortId']: c for c in cohorts['cohorts']}
    data = json.load(open(os.path.join(HERE, 'transfer-results.json'), encoding='utf-8'))
    csv_rows = list(csv.DictReader(open(os.path.join(HERE, 'unseen-transfer.csv'), encoding='utf-8')))
    json_rows = [r for pr in data['pairs'] for sw in pr['sweeps'] for r in sw['rows']]

    # ---- every CSV column, not five of them -------------------------------------------------
    check(len(csv_rows) == len(json_rows), f'CSV has {len(csv_rows)} rows, JSON has {len(json_rows)}')
    cells = 0
    for line, (c, r) in enumerate(zip(csv_rows, json_rows), 2):
        check(set(c) == set(r), f'CSV line {line}: columns differ from the JSON row')
        for key, value in r.items():
            cells += check(c.get(key) == ('' if value is None else str(value)), f'CSV line {line}: {key} is {c.get(key)!r}, JSON has {value!r}')
    print(f'CSV equals JSON in all {len(json_rows[0])} columns of {len(json_rows)} rows ({cells} cells)')

    # ---- the single-character baseline, against the sets it claims to come from --------------
    lift_rows = {}
    gains_checked = programs_checked = empty_rows = 0
    multi_fragment_gains = 0
    summary = {}
    for pr in data['pairs']:
        pid = pr['pairId']
        tr, te = by_id[pr['trainCohort']], by_id[pr['testCohort']]
        tr_ids, te_ids = [p['id'] for p in tr['programs']], [p['id'] for p in te['programs']]
        tr_src = {p['id']: p['text'].encode('ascii') for p in tr['programs']}
        te_src = {p['id']: p['text'].encode('ascii') for p in te['programs']}
        need_tr = {p: frozenset(tr_src[p]) for p in tr_ids}
        need_te = {p: frozenset(te_src[p]) for p in te_ids}
        base_train, base_test, base_bytes = {}, {}, {}
        for k_text, sc in pr['charOptSets'].items():
            chars = frozenset(sc['characters'].encode('ascii'))
            base_train[int(k_text)] = sum(1 for p in tr_ids if need_tr[p] <= chars)
            base_test[int(k_text)] = {p for p in te_ids if need_te[p] <= chars}
            base_bytes[int(k_text)] = len(chars)
        for sw in pr['sweeps']:
            L = sw['maxLen']
            for r in sw['rows']:
                k = r['slots']
                check(r['charOptTrain'] == base_train[k], f'{pid} L={L} K={k}: charOptTrain is {r["charOptTrain"]}, the set spells {base_train[k]}')
                check(r['charOptTest'] == len(base_test[k]), f'{pid} L={L} K={k}: charOptTest is {r["charOptTest"]}, the set spells {len(base_test[k])}')
                check(r['charOptBytes'] == base_bytes[k], f'{pid} L={L} K={k}: charOptBytes is {r["charOptBytes"]}, the set has {base_bytes[k]}')
                # The frozen checker replays a row only when it names a dictionary, and never recounts *Multi.
                for arm, table in ARMS:
                    if r[arm + 'Dict'] is None:
                        empty_rows += check(all(r[arm + x] == 0 for x in ('Train', 'Test', 'Bytes', 'Multi')),
                                            f'{pid} L={L} K={k}: {arm} names no dictionary but reports {[r[arm + x] for x in ("Train", "Test", "Bytes", "Multi")]}')
                    else:
                        entries = sw[table][r[arm + 'Dict']]['entries']
                        check(r[arm + 'Multi'] == sum(1 for w in entries if len(w) > 1) == sw[table][r[arm + 'Dict']]['multiCharacterEntries'],
                              f'{pid} L={L} K={k}: {arm}Multi does not count the multi-character entries of its dictionary')

            # ---- item 3: the unseen-gain attributions --------------------------------------
            recorded = {(g['arm'], g['slots']): g for g in sw['unseenGains']}
            check(len(recorded) == len(sw['unseenGains']), f'{pid} L={L}: duplicate unseen-gain records')
            expected = {(arm, r['slots']) for r in sw['rows'] for arm, _ in ARMS
                        if r[arm + 'Dict'] is not None and r[arm + 'Test'] > r['charOptTest']}
            check(set(recorded) == expected, f'{pid} L={L}: unseen-gain records {sorted(set(recorded) ^ expected)} do not match the rows that gained')
            rows_by_k = {r['slots']: r for r in sw['rows']}
            for (arm, k), g in sorted(recorded.items()):
                r = rows_by_k[k]
                words = [w.encode('ascii') for w in sw[dict(ARMS)[arm]][r[arm + 'Dict']]['entries']]
                spelled = set(replay_spelled(words, te_ids, te_src))
                check(len(spelled) == r[arm + 'Test'], f'{pid} L={L} {arm} K={k}: replay spells {len(spelled)} unseen programs, row says {r[arm + "Test"]}')
                check(g['netTestLift'] == len(spelled) - len(base_test[k]), f'{pid} L={L} {arm} K={k}: netTestLift is wrong')
                gained = sorted(spelled - base_test[k])
                check(g['gainedTestPrograms'] == gained, f'{pid} L={L} {arm} K={k}: gained programs differ from the replay')
                check(sorted(g['fragmentsUsed']) == gained, f'{pid} L={L} {arm} K={k}: attribution does not cover the gained programs')
                singles = [w for w in words if len(w) == 1]
                for p in gained:
                    used = [w.encode('ascii') for w in g['fragmentsUsed'].get(p, [])]
                    for w in used:
                        check(len(w) > 1 and w in words, f'{pid} L={L} {arm} K={k} {p}: {w!r} is not a fragment of the dictionary')
                        check(in_a_valid_parse(w, words, te_src[p]), f'{pid} L={L} {arm} K={k} {p}: {w!r} takes part in no parse of the program')
                    if used:
                        multi_fragment_gains += 1
                    else:  # "uses single characters only" must be true of the program, not only of one parse
                        check(spellable(singles, te_src[p])[0][len(te_src[p])],
                              f'{pid} L={L} {arm} K={k} {p}: recorded as gained without fragments, but single characters do not spell it')
                    programs_checked += 1
                gains_checked += 1

        sw160 = next(sw for sw in pr['sweeps'] if sw['maxLen'] == 160)
        beat = [r for r in sw160['rows'] if r['jointBestTrain'] > r['charOptTrain']]
        r64 = next(r for r in sw160['rows'] if r['slots'] == 64)
        summary[pid] = {
            'budgets': len(beat),
            'train_lift': (min(r['jointBestTrain'] - r['charOptTrain'] for r in beat), max(r['jointBestTrain'] - r['charOptTrain'] for r in beat)),
            'unseen_lift': (min(r['jointBestTest'] - r['charOptTest'] for r in beat), max(r['jointBestTest'] - r['charOptTest'] for r in beat)),
            'k64': (r64['charOptTest'], r64['charFreqDocTest'], r64['jointBestTest'], r64['greedyDPTest'], r64['greedyDPBytes']),
            'greedy_unseen_any_L': sum(r['greedyDPTest'] for sw in pr['sweeps'] if sw['maxLen'] >= 2 for r in sw['rows']),
            'frequency_unseen_k64': sum(r['freqOccTest'] + r['freqDocTest'] for sw in pr['sweeps'] if sw['maxLen'] >= 2 for r in sw['rows'] if r['slots'] == 64),
        }
        lift_rows[pid] = beat
    print(f'single-character baseline of all {len(json_rows)} rows equals the replayed sets (train, unseen, bytes)')
    print(f'{empty_rows} arm cells that name no dictionary report zero everywhere; every other cell counts its multi-character entries correctly')
    print(f'{gains_checked} unseen-gain records replayed, {programs_checked} gained programs: '
          f'{multi_fragment_gains} needed a multi-character fragment')

    # ---- the sentences of RESULTS.md that rest on those numbers --------------------------------
    claims = [
        ('budgets where jointBest (L=160) beat single characters in training, all pairs', sum(s['budgets'] for s in summary.values()), 118),
        ('... per pair', {p: s['budgets'] for p, s in summary.items()}, {'J-80': 40, 'P-80': 1, 'J-160': 47, 'P-160': 30}),
        ('training lift at those budgets, all pairs', (min(s['train_lift'][0] for s in summary.values()), max(s['train_lift'][1] for s in summary.values())), (1, 4)),
        ('... per pair', {p: s['train_lift'] for p, s in summary.items()}, {'J-80': (1, 3), 'P-80': (1, 1), 'J-160': (1, 4), 'P-160': (1, 3)}),
        ('unseen lift at those budgets, all pairs', (min(s['unseen_lift'][0] for s in summary.values()), max(s['unseen_lift'][1] for s in summary.values())), (-3, 0)),
        ('... per pair', {p: s['unseen_lift'] for p, s in summary.items()}, {'J-80': (-3, 0), 'P-80': (0, 0), 'J-160': (-2, 0), 'P-160': (-1, 0)}),
        ('K=64, L=160: charOpt, charFreq, jointBest, greedyDP unseen programs and greedyDP bytes',
         {p: s['k64'] for p, s in summary.items()},
         {'J-80': (9, 7, 9, 0, 1332), 'P-80': (12, 13, 12, 0, 294), 'J-160': (4, 7, 4, 0, 1953), 'P-160': (36, 32, 36, 0, 808)}),
        ('unseen programs spelled by greedyDP at any budget and any L >= 2', sum(s['greedy_unseen_any_L'] for s in summary.values()), 0),
        ('unseen programs spelled by the frequency arms at K=64, any L >= 2', sum(s['frequency_unseen_k64'] for s in summary.values()), 0),
        ('unseen gains that needed a multi-character fragment (T4: 0.00% multi-character lift)', multi_fragment_gains, 0),
    ]
    for label, got, want in claims:
        ok = check(got == want, f'RESULTS.md claim does not reproduce: {label}: computed {got}, RESULTS.md says {want}')
        print(f'{"ok  " if ok else "FAIL"} {label}: {got}')
    if FAILED:
        print('\n'.join('FAILED: ' + f for f in FAILED[:40]))
        return 1
    print('ALL SUPPLEMENTARY CHECKS PASSED: the numbers RESULTS.md quotes are the numbers a replay gives')
    return 0


if __name__ == '__main__':
    sys.exit(main())
