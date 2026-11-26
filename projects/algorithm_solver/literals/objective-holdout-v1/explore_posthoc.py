#!/usr/bin/env python3
"""Post hoc, exploratory: measurements two reviews asked for after the test sets were scored.

Nothing here was preregistered and no rule was chosen with it. It reads the frozen headers,
the committed result files and the corpus, and writes out/posthoc-exploration.json.

    python3 explore_posthoc.py [--jobs N]        # needs zstd for part 4

1. Equal size. The token-gain order and the BPE order, both cut at the same number of
   fragments, on every set. The orders are read from the frozen 4,096-cap headers, whose
   entries are stored in the order they were chosen. The ends (84 and 3,924 fragments) and
   the byte-selected size (1,408) must equal the frozen results, or the script stops.
2. Subsets of the unseen problems: by language, and by whether the file's author also wrote
   a training file.
3. How often the token-selected fragments occur in the training text.
4. zstd with lean framing: no checksum and no dictionary id in each frame.
5. What the project sample is made of.
"""
import argparse
import csv
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bits_oh as B  # noqa: E402

LIT = HERE.parent
SETS = {'train': (HERE / 'frozen' / 'sets' / 'train.json', LIT), 'dev': (HERE / 'frozen' / 'sets' / 'dev.json', LIT),
        'fresh': (HERE / 'sets' / 'fresh.json', HERE), 'project': (HERE / 'sets' / 'project.json', HERE)}
GRID = (84, 200, 400, 600, 900, 1200, 1408, 1700, 2000, 2350, 2700, 3300, 3924)

_DOCS = None


def load(name):
    manifest, root = SETS[name]
    spec = json.loads(manifest.read_text())
    return spec, [(root / f['path']).read_bytes() for f in spec['files']]


def order(name):
    entries, _, _ = B.parse_header((HERE / 'frozen' / f'{name}.boh').read_bytes())
    return [e for e in entries if len(e) == 1], [e for e in entries if len(e) > 1]


def _init(docs):
    global _DOCS
    _DOCS = docs


def _tokens(job):
    key, entries = job
    d = B.Dictionary(entries)
    return key, {s: sum(len(B.parse_tokens(d.edges(raw))) for raw in docs) for s, docs in _DOCS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    specs, docs = {}, {}
    for name in SETS:
        specs[name], docs[name] = load(name)
    res = {s: json.loads((HERE / 'out' / f'results-{s}.json').read_text()) for s in SETS}
    out = {'schema': 'gamma.bits-objective-holdout.posthoc-exploration.v1',
           'note': 'post hoc and exploratory; computed after the test sets were scored'}

    # 1. equal size
    singles, tok_order = order('token-K4096')
    singles_b, bpe_order = order('bpe-K4096')
    assert singles == singles_b
    jobs = [((rule, m), singles + frags[:m]) for m in GRID for rule, frags in (('token', tok_order), ('bpe', bpe_order))]
    with Pool(args.jobs, initializer=_init, initargs=(docs,)) as pool:
        counted = dict(pool.map(_tokens, jobs, chunksize=1))
    for s in SETS:
        h = res[s]['headers']
        assert counted[('token', 84)][s] == h['token-K256']['min_tokens'] and counted[('bpe', 84)][s] == h['bpe-K256']['min_tokens']
        assert counted[('token', 3924)][s] == h['token-K4096']['min_tokens'] and counted[('bpe', 3924)][s] == h['bpe-K4096']['min_tokens']
        assert counted[('token', 1408)][s] == h['bytes-K4096']['min_tokens']
    out['equal_size'] = {'grid': list(GRID), 'tokens': {rule: {s: [counted[(rule, m)][s] for m in GRID] for s in SETS} for rule in ('token', 'bpe')},
                         'ends_match_frozen_results': True}

    # 2. subsets of the unseen problems
    manifest = json.loads((LIT / 'codenet-replication-v1' / 'manifest.json').read_text())
    train_authors = {'python': set(), 'javascript': set()}
    for pair in manifest['splits']['primary']['pairs']:
        for lang in train_authors:
            train_authors[lang].add(pair[lang]['u_id'])
    any_author = train_authors['python'] | train_authors['javascript']
    with open(HERE / 'out' / 'per-file-fresh.csv') as fh:
        rows = list(csv.DictReader(fh))
    files = specs['fresh']['files']
    assert [r['file'] for r in rows] == [f['path'] for f in files]

    def cut(label, keep):
        idx = [i for i, f in enumerate(files) if keep(f)]
        row = {'subset': label, 'files': len(idx), 'bytes': sum(files[i]['bytes'] for i in idx)}
        for cap in (256, 4096):
            a = sum(int(rows[i][f'token-K{cap}:tokens']) for i in idx)
            b = sum(int(rows[i][f'bpe-K{cap}:tokens']) for i in idx)
            row[f'token_gain_tokens_K{cap}'] = a
            row[f'bpe_tokens_K{cap}'] = b
            row[f'token_vs_bpe_percent_K{cap}'] = round(100.0 * (a - b) / b, 4)
        return row

    out['unseen_subsets'] = [
        cut('all', lambda f: True),
        cut('author wrote no training file', lambda f: f['u_id'] not in any_author),
        cut('author wrote a training file', lambda f: f['u_id'] in any_author),
        cut('author wrote a training file in the same language', lambda f: f['u_id'] in train_authors[f['lang']]),
        cut('Python', lambda f: f['lang'] == 'python'),
        cut('JavaScript', lambda f: f['lang'] == 'javascript'),
        cut('JavaScript, author wrote a training file', lambda f: f['lang'] == 'javascript' and f['u_id'] in any_author),
    ]
    train_count = Counter(pair[lang]['u_id'] for pair in manifest['splits']['primary']['pairs'] for lang in ('python', 'javascript'))
    fresh_count = Counter(f['u_id'] for f in files)
    top = max(train_count, key=train_count.get)
    out['most_prolific_training_author'] = {'training_files': train_count[top], 'unseen_files': fresh_count.get(top, 0)}

    # 3. occurrences of the token-selected fragments in the training text
    ent = json.loads((HERE / 'out' / 'entries-train.json').read_text())['token-K4096']
    frags = [bytes.fromhex(h) for h in ent['entry_hex']]

    def occurrences(b):
        n = 0
        for d in docs['train']:
            i = d.find(b)
            while i >= 0:
                n += 1
                i = d.find(b, i + 1)
        return n

    occ = [occurrences(b) for b in frags]
    one = [i for i, u in enumerate(ent['train_units']) if u == 1]
    out['token_selected_fragments'] = {
        'fragments': len(frags),
        'occur_once_in_training_text': sum(1 for x in occ if x == 1),
        'used_by_one_training_problem': len(one),
        'of_those_occur_once': sum(1 for i in one if occ[i] == 1),
        'of_those_median_uses_in_training_parse': statistics.median(ent['uses'][i] for i in one),
        'of_those_median_length': statistics.median(len(frags[i]) for i in one),
    }

    # 4. zstd with lean framing
    zstd = shutil.which('zstd')
    if zstd:
        lean = {'version': subprocess.run([zstd, '--version'], capture_output=True, text=True).stdout.strip(), 'sets': {}}
        dict_path = HERE / 'frozen' / 'zstd-train-8k.dict'
        for s in SETS:
            with tempfile.TemporaryDirectory() as td:
                td = Path(td)
                src = td / 'src'
                src.mkdir()
                paths = []
                for i, raw in enumerate(docs[s]):
                    p = src / f'f{i:05d}'
                    p.write_bytes(raw)
                    paths.append(str(p))
                row = {}
                for label, extra in (('trained_dictionary', ['-D', str(dict_path)]), ('no_dictionary', [])):
                    z = td / label
                    back = td / (label + '-back')
                    z.mkdir()
                    back.mkdir()
                    subprocess.run([zstd, '-19', '-q', '-f', '--no-check', '--no-dictID', '--output-dir-flat', str(z)] + extra + paths, check=True)
                    frames = sorted(z.iterdir())
                    subprocess.run([zstd, '-d', '-q', '-f', '--output-dir-flat', str(back)] + extra + [str(f) for f in frames], check=True)
                    assert all((back / Path(p).name).read_bytes() == raw for p, raw in zip(paths, docs[s]))
                    frames_bytes = sum(f.stat().st_size for f in frames)
                    row[label] = {'frames': frames_bytes, 'complete': frames_bytes + (dict_path.stat().st_size if extra else 0)}
                lean['sets'][s] = row
        out['zstd_lean_framing'] = lean

    # 5. the project sample
    kinds = Counter((f['source_path'].split('/')[0] if '/' in f['source_path'] else f['source_path']) for f in specs['project']['files'])
    out['project_sample_by_top_level'] = dict(sorted(kinds.items(), key=lambda kv: -kv[1]))

    (HERE / 'out' / 'posthoc-exploration.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: out[k] for k in ('unseen_subsets', 'most_prolific_training_author', 'token_selected_fragments', 'project_sample_by_top_level')}, indent=1))
    g = out['equal_size']
    for i, m in enumerate(GRID):
        print(m, ' '.join(f'{s}:{100.0 * (g["tokens"]["token"][s][i] - g["tokens"]["bpe"][s][i]) / g["tokens"]["bpe"][s][i]:+.1f}%' for s in SETS))
    if zstd:
        print(json.dumps(out['zstd_lean_framing']['sets']))


if __name__ == '__main__':
    main()
