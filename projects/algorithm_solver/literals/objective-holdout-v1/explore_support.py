#!/usr/bin/env python3
"""Post hoc, exploratory: how does a fragment's support in training relate to
whether it pays for its storage on the test sets?

Written after the test sets were scored. It reads the committed result files
and the training files, and changes nothing. Nothing here was preregistered
and no rule was chosen with it.

    python3 explore_support.py

For each frozen 4,096-cap dictionary it writes, to out/support-exploration.json:
  - fragments binned by the number of training problems whose parse used them,
    with the share used and the share that pay rent on each test set;
  - how well each training-side signal ranks the fragments that pay rent
    (area under the ROC curve; 0.5 is chance).
"""
import bisect
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BINS = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 9), (10, 19), (20, 10 ** 9)]
ARMS = ('token-K4096', 'bytes-K4096', 'bpe-K4096')


def auc(score, label):
    pos = [s for s, l in zip(score, label) if l]
    neg = len(label) - len(pos)
    if not pos or not neg:
        return None
    srt = sorted(score)

    def rank(v):
        return (bisect.bisect_left(srt, v) + bisect.bisect_right(srt, v) + 1) / 2

    return round((sum(rank(s) for s in pos) - len(pos) * (len(pos) + 1) / 2) / (len(pos) * neg), 4)


def main():
    ent = {s: json.loads((HERE / 'out' / f'entries-{s}.json').read_text()) for s in ('train', 'fresh', 'project')}
    docs = [(HERE.parent / f['path']).read_bytes()
            for f in json.loads((HERE / 'frozen' / 'sets' / 'train.json').read_text())['files']]

    def occurrences(b):
        n = 0
        for d in docs:
            i = d.find(b)
            while i >= 0:
                n += 1
                i = d.find(b, i + 1)
        return n

    out = {'schema': 'gamma.bits-objective-holdout.support-exploration.v1',
           'note': 'post hoc and exploratory; computed after the test sets were scored', 'dictionaries': {}}
    for arm in ARMS:
        t = ent['train'][arm]
        frags = [bytes.fromhex(h) for h in t['entry_hex']]
        signals = {
            'training problems that used it': t['train_units'],
            'training files that contain it': [sum(1 for d in docs if b in d) for b in frags],
            'uses in the training parse': t['uses'],
            'overlapping occurrences in training': [occurrences(b) for b in frags],
            'shorter length': [-len(b) for b in frags],
            'net bytes saved in training': t['rent_bits'],
        }
        row = {'fragments': len(frags), 'never_used_in_training_parse': sum(1 for u in t['train_units'] if u == 0),
               'bins': [], 'auc': {}}
        for lo, hi in BINS:
            idx = [i for i, u in enumerate(t['train_units']) if lo <= u <= hi]
            b = {'training_problems': str(lo) if lo == hi else (f'{lo}+' if hi > 10 ** 6 else f'{lo}-{hi}'), 'fragments': len(idx)}
            for s in ('fresh', 'project'):
                b[f'used_{s}'] = sum(1 for i in idx if ent[s][arm]['uses'][i] > 0)
                b[f'pay_rent_{s}'] = sum(1 for i in idx if ent[s][arm]['rent_bits'][i] > 0)
            row['bins'].append(b)
        for s in ('fresh', 'project'):
            label = [x > 0 for x in ent[s][arm]['rent_bits']]
            row['auc'][s] = {name: auc(v, label) for name, v in signals.items()}
        out['dictionaries'][arm] = row
        print(arm, json.dumps(row['auc']))
    (HERE / 'out' / 'support-exploration.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
