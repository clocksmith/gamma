#!/usr/bin/env python3
"""POST HOC. What is inside the three frozen 3,924-fragment dictionaries, and does the token difference
hold across problem subsets? Computed after closure-holdout-v1 was scored; decides no rule.

    python3 -I explore_dictionary.py

For bpe, token and closed (frozen/dictionaries.json, 4,096 cap):
  per fragment: length; raw occurrences in the training text (overlapping); uses in the exact
  minimum-token training parse; distinct training problems whose parse uses it; uses on every test set.
  per set: tokens, single-byte (or escape) tokens, source bytes.
  per set and subset (language; for CodeNet sets, whether the file's author also wrote a training
  file): paired differences token - bpe and closed - bpe, with 95% bootstrap intervals over units
  (CodeNet problem or repository file), 2,000 resamples, seed 0.
Writes out/posthoc-dictionary.json.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

SETS = {'train': (OH / 'frozen/sets/train.json', LIT), 'fresh': (OH / 'sets/fresh.json', OH),
        'project': (OH / 'sets/project.json', OH), 'fresh2': (HERE / 'sets/fresh2.json', HERE),
        'project-python': (HERE / 'sets/project-python.json', HERE),
        'project-javascript': (HERE / 'sets/project-javascript.json', HERE)}
ARMS = ('bpe', 'token', 'closed')
_D = None


def init(d):
    global _D
    _D = d


def parse_all(entries):
    """Per file: list of symbol ids of the exact minimum-token parse."""
    d = B.Dictionary(entries)
    return [B.parse_tokens(d.edges(raw)) for raw in _D]


def boot(diffs_by_unit, reps=2000, seed=0):
    units = sorted(diffs_by_unit)
    a = [diffs_by_unit[u][0] for u in units]
    b = [diffs_by_unit[u][1] for u in units]
    point = 100.0 * (sum(a) - sum(b)) / sum(b)
    rng = random.Random(seed)
    vals = []
    n = len(units)
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        sa = sum(a[i] for i in idx)
        sb = sum(b[i] for i in idx)
        vals.append(100.0 * (sa - sb) / sb)
    vals.sort()
    return {'units': n, 'percent': round(point, 2), 'ci95': [round(vals[int(0.025 * reps)], 2), round(vals[int(0.975 * reps) - 1], 2)]}


def main():
    frozen = json.loads((HERE / 'frozen/dictionaries.json').read_text())
    A = frozen['alphabet']
    dicts = {a: [bytes.fromhex(h) for h in frozen['dictionaries'][f'{a}-K4096']] for a in ARMS}
    train_manifest = json.loads(SETS['train'][0].read_text())['files']
    train_docs = [(LIT / f['path']).read_bytes() for f in train_manifest]
    train_authors = set()
    m = json.loads((LIT / 'codenet-replication-v1' / 'manifest.json').read_text())
    for p in m['splits']['primary']['pairs']:
        for lang in ('python', 'javascript'):
            train_authors.add(p[lang]['u_id'])
    out = {'note': 'post hoc: computed after closure-holdout-v1 was scored; decides no rule', 'alphabet': A, 'rules': {}, 'sets': {}}
    parses = {}
    files_by_set = {}
    for name, (spec, root) in SETS.items():
        files = json.loads(spec.read_text())['files']
        docs = [(root / f['path']).read_bytes() for f in files]
        files_by_set[name] = (files, docs)
        with Pool(8, initializer=init, initargs=(docs,)) as pool:
            res = pool.map(parse_all, [dicts[a] for a in ARMS])
        parses[name] = dict(zip(ARMS, res))
    for a in ARMS:
        entries = dicts[a]
        frag = entries[A:]
        # raw overlapping occurrences in the training text
        raw_occ = []
        for f in frag:
            c = 0
            for raw in train_docs:
                i = raw.find(f)
                while i >= 0:
                    c += 1
                    i = raw.find(f, i + 1)
            raw_occ.append(c)
        uses_train = Counter()
        problems = defaultdict(set)
        for f_rec, syms in zip(train_manifest, parses['train'][a]):
            for s in syms:
                if s >= A and s < len(entries):
                    uses_train[s] += 1
                    problems[s].add(f_rec['unit'])
        rule = {'length': [len(f) for f in frag], 'train_raw_occurrences': raw_occ,
                'train_parse_uses': [uses_train[A + i] for i in range(len(frag))],
                'train_problems_using': [len(problems[A + i]) for i in range(len(frag))], 'uses': {}}
        for name in SETS:
            if name == 'train':
                continue
            u = Counter()
            for syms in parses[name][a]:
                for s in syms:
                    if s >= A and s < len(entries):
                        u[s] += 1
            rule['uses'][name] = [u[A + i] for i in range(len(frag))]
        out['rules'][a] = rule
    for name, (files, docs) in files_by_set.items():
        s = {'files': len(files), 'bytes': sum(map(len, docs)), 'by_rule': {}, 'subsets': {}}
        per_file = {}
        for a in ARMS:
            d = B.Dictionary(dicts[a])
            toks = [len(p) for p in parses[name][a]]
            single = [sum(1 for x in p if x == d.ESC or len(d.entries[x]) == 1) for p in parses[name][a]]
            per_file[a] = toks
            s['by_rule'][a] = {'tokens': sum(toks), 'single_byte_tokens': sum(single)}
        subsets = {'all': lambda f: True, 'python': lambda f: f['lang'] == 'python', 'javascript': lambda f: f['lang'] == 'javascript'}
        if name in ('fresh', 'fresh2'):
            subsets['author_also_in_training'] = lambda f: f.get('u_id') in train_authors
            subsets['author_not_in_training'] = lambda f: f.get('u_id') not in train_authors
        for label, keep in subsets.items():
            row = {}
            for a in ('token', 'closed'):
                by_unit = defaultdict(lambda: [0, 0])
                for i, f in enumerate(files):
                    if keep(f):
                        by_unit[f['unit']][0] += per_file[a][i]
                        by_unit[f['unit']][1] += per_file['bpe'][i]
                if by_unit:
                    row[f'{a}_vs_bpe'] = boot(dict(by_unit))
            if row:
                s['subsets'][label] = row
        out['sets'][name] = s
        print(name, {k: v.get('token_vs_bpe', {}).get('percent') for k, v in s['subsets'].items()}, flush=True)
    (HERE / 'out' / 'posthoc-dictionary.json').write_text(json.dumps(out) + '\n')


if __name__ == '__main__':
    main()
