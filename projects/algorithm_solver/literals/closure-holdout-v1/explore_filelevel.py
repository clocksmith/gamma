#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Does a statistic computed before fitting predict, file by file, how much open token gain beats
or trails BPE? Fits on `dev` files only; reports the fit's prediction for the scored sets as a post hoc sanity check.

    python3 -I explore_filelevel.py

Per dev file: shared coverage (share of its 12-byte windows whose string occurs in >= 2 training files), length,
language, and closest-training-file 8-byte shingle Jaccard. Outcome: open (exact) minus BPE tokens at 84 and at
3,924 fragments, as a percentage of BPE tokens for that file. Reports Spearman rank correlations, a least-squares
line of the outcome on each predictor, and that line's prediction of the pooled gap on every other set.
Writes out/dev-filelevel.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

SETS = {'dev': (OH / 'frozen/sets/dev.json', LIT, 'dev'), 'fresh': (OH / 'sets/fresh.json', OH, 'post hoc'),
        'project': (OH / 'sets/project.json', OH, 'post hoc'), 'fresh2': (HERE / 'sets/fresh2.json', HERE, 'post hoc'),
        'project-python': (HERE / 'sets/project-python.json', HERE, 'post hoc'),
        'project-javascript': (HERE / 'sets/project-javascript.json', HERE, 'post hoc')}


def chain(path):
    return [bytes.fromhex(line.split()[5]) for line in Path(path).read_text().splitlines() if line.startswith('E ') and len(line.split()) == 6]


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((y - mb) ** 2 for y in b) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def line(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx if sxx else 0.0
    return my - b * mx, b


def main():
    frozen = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())
    A = frozen['alphabet']
    train_files = json.loads((OH / 'frozen/sets/train.json').read_text())['files']
    train = [(LIT / f['path']).read_bytes() for f in train_files]
    singles = [bytes([b]) for b in sorted({b for r in train for b in r})]
    bpe = [bytes.fromhex(h) for h in frozen['dictionaries']['bpe-K4096']]
    opn = singles + chain(HERE / 'out' / 'exact' / 'exact-entry-s1-whole.txt')[len(singles):]
    dicts = {(a, m): B.Dictionary(order[:A + m]) for a, order in (('bpe', bpe), ('open', opn)) for m in (84, 3924)}
    seen = {}
    for raw in train:
        for g in {raw[j:j + 12] for j in range(len(raw) - 11)}:
            seen[g] = seen.get(g, 0) + 1
    train_sh = {}
    for f, raw in zip(train_files, train):
        train_sh.setdefault(f['lang'], []).append({raw[j:j + 8] for j in range(len(raw) - 7)})

    def features(raw, lang):
        wins = [raw[j:j + 12] for j in range(len(raw) - 11)]
        cov = sum(1 for g in wins if seen.get(g, 0) >= 2) / max(1, len(wins))
        sh = {raw[j:j + 8] for j in range(len(raw) - 7)}
        jac = max((len(sh & t) / len(sh | t) for t in train_sh.get(lang, [])), default=0.0) if sh else 0.0
        return {'coverage': cov, 'length': len(raw), 'python': 1.0 if lang == 'python' else 0.0, 'jaccard': jac}

    rows = {}
    for name, (spec, root, status) in SETS.items():
        out = []
        for f in json.loads(spec.read_text())['files']:
            raw = (root / f['path']).read_bytes()
            r = features(raw, f['lang'])
            for m in (84, 3924):
                tb = len(B.parse_tokens(dicts[('bpe', m)].edges(raw)))
                to = len(B.parse_tokens(dicts[('open', m)].edges(raw)))
                r[f'bpe{m}'], r[f'open{m}'] = tb, to
                r[f'gap{m}'] = 100.0 * (to - tb) / tb
            out.append(r)
        rows[name] = out
        print(name, len(out), 'files', flush=True)
    dev = rows['dev']
    result = {'note': 'fit on dev only; predictions for other sets are post hoc checks', 'predictors': {}}
    for m in (84, 3924):
        y = [r[f'gap{m}'] for r in dev]
        for p in ('coverage', 'length', 'python', 'jaccard'):
            x = [r[p] for r in dev]
            rho = pearson(rank(x), rank(y))
            a, b = line(x, y)
            preds = {}
            for name, rs in rows.items():
                mean_x = sum(r[p] for r in rs) / len(rs)
                actual = 100.0 * (sum(r[f'open{m}'] for r in rs) - sum(r[f'bpe{m}'] for r in rs)) / sum(r[f'bpe{m}'] for r in rs)
                preds[name] = {'mean_predictor': round(mean_x, 4), 'line_prediction': round(a + b * mean_x, 2), 'actual_pooled_gap': round(actual, 2)}
            result['predictors'][f'{p}@{m}'] = {'spearman_dev_files': round(rho, 3), 'line': [round(a, 3), round(b, 3)], 'sets': preds}
            print(f'@{m} {p:9} rho={rho:+.3f} | ' + ' | '.join(f'{k}: pred {v["line_prediction"]:+.1f} act {v["actual_pooled_gap"]:+.1f}' for k, v in preds.items()), flush=True)
    (HERE / 'out' / 'dev-filelevel.json').write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
