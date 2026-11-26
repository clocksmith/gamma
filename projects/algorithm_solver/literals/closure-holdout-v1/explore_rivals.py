#!/usr/bin/env python3
"""POST HOC. Written after closure-holdout-v1 was scored. Tests rival explanations of the
closure result on the already-scored sets; nothing here is preregistered or decides a rule.

    python3 -I explore_rivals.py --work WORKDIR

Rules, all built from engine_closed.c on CodeNet `primary`:
  bpe, token, closed        the three frozen arms (rebuilt; train.py checks they match)
  support2                  open token gain, candidates used by at least two training problems
                            (frozen engine policy p2-nowhole, groups = CodeNet problem)
  closedsupport2            closed token gain with the same support filter
  len8                      open token gain with fragments of at most 8 bytes
Reports tokens relative to BPE at 84, 1,964 and 3,924 fragments on every set, the mean fragment
length, and the single-byte share. Writes out/posthoc-rivals.json.
"""
import argparse
import json
import os
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

SETS = {'train': (OH / 'frozen/sets/train.json', LIT), 'dev': (OH / 'frozen/sets/dev.json', LIT),
        'fresh': (OH / 'sets/fresh.json', OH), 'project': (OH / 'sets/project.json', OH),
        'fresh2': (HERE / 'sets/fresh2.json', HERE), 'project-python': (HERE / 'sets/project-python.json', HERE),
        'project-javascript': (HERE / 'sets/project-javascript.json', HERE)}
RULES = {'bpe': ('bpe', 's1-whole', 16), 'token': ('greedy-entry', 's1-whole', 16), 'closed': ('greedy-closed', 's1-whole', 16),
         'support2': ('greedy-entry', 'p2-nowhole', 16), 'closedsupport2': ('greedy-closed', 'p2-nowhole', 16),
         'len8': ('greedy-entry', 's1-whole', 8)}
SIZES = [84, 1964, 3924]
_D = None


def chain(p):
    return [bytes.fromhex(line.split()[5]) for line in Path(p).read_text().splitlines() if line.startswith('E ')]


def init(docs):
    global _D
    _D = docs


def tokens(entries):
    d = B.Dictionary(entries)
    t = s = 0
    for raw in _D:
        sy = B.parse_tokens(d.edges(raw))
        t += len(sy)
        s += sum(1 for x in sy if x == d.ESC or len(d.entries[x]) == 1)
    return t, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    work = Path(ap.parse_args().work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    train = json.loads(SETS['train'][0].read_text())['files']
    (work / 'train.list').write_text('\n'.join(str(LIT / f['path']) for f in train) + '\n')
    units = sorted({f['unit'] for f in train})
    (work / 'groups.txt').write_text('\n'.join(str(units.index(f['unit'])) for f in train) + '\n')
    subprocess.run(['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(work / 'engine_closed'), str(HERE / 'engine_closed.c'), '-lm'],
                   check=True, cwd=HERE)
    env = dict(os.environ, FSV3_RECEIPT='manifest=primary pool=both cuts=none impl=engine_closed run=closure-posthoc',
               FSV3_GROUPS=str(work / 'groups.txt'))
    docs_train = [(LIT / f['path']).read_bytes() for f in train]
    singles = [bytes([b]) for b in sorted({b for r in docs_train for b in r})]
    orders = {}
    for name, (mode, policy, L) in RULES.items():
        out = work / f'{name}.txt'
        subprocess.run([str(work / 'engine_closed'), mode, policy, str(L), '4096', '300', str(work / 'train.list'), str(out)],
                       env=env, check=True)
        e = chain(out)
        assert e[:len(singles)] == singles, name
        orders[name] = e[len(singles):]
    frozen = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())['dictionaries']
    for a in ('bpe', 'token', 'closed'):
        if [h for h in frozen[f'{a}-K4096']] != [x.hex() for x in singles + orders[a][:3924]]:
            raise SystemExit(f'{a} does not match the frozen dictionary')
    result = {'note': 'post hoc: computed after closure-holdout-v1 was scored; no rule is decided here',
              'sizes': SIZES, 'mean_fragment_length_3924': {a: round(sum(map(len, o[:3924])) / 3924, 2) for a, o in orders.items()},
              'tokens': {}, 'single_byte_tokens': {}}
    for name, (spec, root) in SETS.items():
        docs = [(root / f['path']).read_bytes() for f in json.loads(spec.read_text())['files']]
        jobs = [(a, m) for a in RULES for m in SIZES]
        with Pool(8, initializer=init, initargs=(docs,)) as pool:
            res = dict(zip(jobs, pool.map(tokens, [singles + orders[a][:m] for a, m in jobs])))
        result['tokens'][name] = {a: [res[(a, m)][0] for m in SIZES] for a in RULES}
        result['single_byte_tokens'][name] = {a: [res[(a, m)][1] for m in SIZES] for a in RULES}
        print(name.ljust(18), ' | '.join(f'@{m}: ' + ' '.join(f'{a} {100 * (res[(a, m)][0] / res[("bpe", m)][0] - 1):+.1f}'
                                                             for a in RULES if a != 'bpe') for m in SIZES), flush=True)
    (HERE / 'out' / 'posthoc-rivals.json').write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
