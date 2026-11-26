#!/usr/bin/env python3
"""Why did each unseen file fail in the earlier zero-escape transfer test?

Reads the frozen `witness-length-sweep-v1` transfer results and the frozen
`witness-scaling-v1` cohorts; changes neither. For every stored dictionary and
every unseen (-b) file it did not spell, it names the first reason that holds:

  unseen byte         the file has a byte that no training (-a) file has, so
                      no dictionary built from the training files can spell it;
  uncovered position  some position lies under no match of any entry (the
                      byte's single-character entry is missing and no fragment
                      matches around it there);
  cannot tile         every position lies under some match, yet no sequence
                      of entries spells the file from start to end.

An uncovered position proves failure. Having none does not prove success:
`abc` with {ab, bc} is covered everywhere and has no parse. The script checks
each spelled count against the stored one before it reports anything.

    python3 audit_zero_escape_misses.py [OUT.json]

Standard library only. These artifacts are ASCII, so bytes and characters agree.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWEEP = HERE.parent / 'witness-length-sweep-v1'
COHORTS = HERE.parent / 'witness-scaling-v1' / 'cohorts.json'
REASONS = ('unseen byte', 'uncovered position', 'cannot tile')
ARMS = ('charOpt', 'charFreqDoc', 'freqOcc', 'freqDoc', 'jointBest', 'greedyDP')


def classify(words, files, train_alphabet):
    """Returns (spelled, counts by reason) over the given files."""
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    spelled = 0
    counts = dict.fromkeys(REASONS, 0)
    for s in files:
        n = len(s)
        covered = bytearray(n)
        starts = [[] for _ in range(n)]
        for i in range(n):
            for w in by_first.get(s[i], ()):
                if s.startswith(w, i):
                    starts[i].append(len(w))
                    covered[i:i + len(w)] = b'\x01' * len(w)
        reach = bytearray(n + 1)
        reach[0] = 1
        for i in range(n):
            if reach[i]:
                for l in starts[i]:
                    reach[i + l] = 1
        if reach[n]:
            spelled += 1
        elif not train_alphabet.issuperset(s):
            counts['unseen byte'] += 1
        elif 0 in covered:
            counts['uncovered position'] += 1
        else:
            counts['cannot tile'] += 1
    return spelled, counts


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'zero-escape-miss-audit.json'
    cohorts = {c['cohortId']: c for c in json.loads(COHORTS.read_text())['cohorts']}
    data = json.loads((SWEEP / 'transfer-results.json').read_text())
    totals = {arm: dict.fromkeys(REASONS + ('spelled', 'cells', 'file_checks'), 0) for arm in ARMS}
    multi_totals = {arm: dict.fromkeys(REASONS + ('spelled', 'cells', 'file_checks'), 0) for arm in ARMS}
    at_64 = []
    train_gain = dict.fromkeys(REASONS + ('spelled', 'cells', 'file_checks'), 0)
    for pr in data['pairs']:
        train = [p['text'].encode('ascii') for p in cohorts[pr['trainCohort']]['programs']]
        test = [p['text'].encode('ascii') for p in cohorts[pr['testCohort']]['programs']]
        alphabet = frozenset(b''.join(train))
        unseen_files = sum(1 for s in test if not alphabet.issuperset(s))
        cache = {}

        def run(words):
            key = tuple(words)
            if key not in cache:
                cache[key] = classify(words, test, alphabet)
            return cache[key]

        ranked = [w.encode('ascii') for w in pr['charFreqRanked']]
        for sw in pr['sweeps']:
            L = sw['maxLen']
            focc = [w.encode('ascii') for w in sw['freqOccTop']]
            fdoc = [w.encode('ascii') for w in sw['freqDocTop']]
            joint = {k: [w.encode('ascii') for w in d['entries']] for k, d in sw['jointDictionaries'].items()}
            greedy = {k: [w.encode('ascii') for w in d['entries']] for k, d in sw['greedyDictionaries'].items()}
            for r in sw['rows']:
                k = r['slots']
                dicts = {
                    'charOpt': [bytes([c]) for c in pr['charOptSets'][str(k)]['characters'].encode('ascii')],
                    'charFreqDoc': ranked[:k],
                    'freqOcc': focc[:k],
                    'freqDoc': fdoc[:k],
                    'jointBest': joint[r['jointBestDict']] if r['jointBestDict'] is not None else None,
                    'greedyDP': greedy[r['greedyDPDict']] if r['greedyDPDict'] is not None else None,
                }
                row64 = {'pair': pr['pairId'], 'maxLen': L, 'testFiles': len(test), 'filesWithUnseenByte': unseen_files}
                for arm in ARMS:
                    words = dicts[arm]
                    if words is None:
                        continue
                    spelled, counts = run(words)
                    if spelled != r[arm + 'Test']:
                        raise SystemExit(f'{pr["pairId"]} L={L} K={k} {arm}: spelled {spelled}, stored {r[arm + "Test"]}')
                    has_multi = any(len(w) > 1 for w in words)
                    for bucket in ([totals[arm]] + ([multi_totals[arm]] if has_multi else [])):
                        bucket['cells'] += 1
                        bucket['file_checks'] += len(test)
                        bucket['spelled'] += spelled
                        for reason in REASONS:
                            bucket[reason] += counts[reason]
                    if k == 64:
                        row64[arm] = {'spelled': spelled, **counts}
                    if arm == 'jointBest' and L == 160 and r['jointBestTrain'] > r['charOptTrain']:
                        train_gain['cells'] += 1
                        train_gain['file_checks'] += len(test)
                        train_gain['spelled'] += spelled
                        for reason in REASONS:
                            train_gain[reason] += counts[reason]
                if k == 64:
                    at_64.append(row64)
        print(f'{pr["pairId"]}: {len(test)} unseen files, {unseen_files} with a byte no training file has', flush=True)
    out = {
        'schema': 'gamma.bits-objective-holdout.zero-escape-miss-audit.v1',
        'source': 'witness-length-sweep-v1/transfer-results.json, cohortsSha256 ' + data['cohortsSha256'],
        'reasons': list(REASONS),
        'all_cells_by_arm': totals,
        'cells_whose_dictionary_has_a_multi_byte_entry_by_arm': multi_totals,
        'jointBest_L160_budgets_that_beat_single_characters_in_training': train_gain,
        'at_64_slots': at_64,
    }
    out_path.write_text(json.dumps(out, indent=1) + '\n')
    for arm in ARMS:
        t = totals[arm]
        miss = t['file_checks'] - t['spelled']
        print(f'{arm:12s} cells {t["cells"]:5d}  misses {miss:7d}  '
              + '  '.join(f'{reason}: {t[reason]}' for reason in REASONS))


if __name__ == '__main__':
    main()
