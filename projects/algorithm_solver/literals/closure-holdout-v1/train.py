#!/usr/bin/env python3
"""Train the three arms on CodeNet `primary` (the objective-holdout-v1 training
split) and freeze their dictionaries. Reads no test file.

    python3 -I train.py --work WORKDIR

Arms (same candidate pool, same exact parser, 16-byte limit, policy s1-whole):
  bpe     byte pair encoding: pair-count objective, constituent-closed
  token   greedy exact token gain: gain objective, open (any substring)
  closed  greedy exact token gain restricted to concatenations of two members
          of the current dictionary: gain objective, constituent-closed
Caps 256 and 4,096 symbols: the training alphabet, one escape, and the first
CAP - alphabet - 1 multi-byte entries of each chain.

The bpe and token chains must reproduce the frozen objective-holdout-v1
dictionaries entry for entry; the run stops otherwise.
Writes frozen/dictionaries.json and frozen/train-summary.json.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
OH = LITERALS / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

CODENET = LITERALS / 'codenet-replication-v1'
SRC = HERE / 'engine_closed.c'
FROZEN_ENGINE = LITERALS / 'fixed-source-v3' / 'engine.c'
FROZEN_ENGINE_SHA256 = '7331f1eb6d7866c6b71fbb0c19be6b1f8afdfa6ff9003c95604fa9051f8db19f'
CAPS = (256, 4096)
MAX_LEN = 16
KMAX = 4096
MODES = {'bpe': 'bpe', 'token': 'greedy-entry', 'closed': 'greedy-closed'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def chain_entries(path):
    out = []
    for line in Path(path).read_text().splitlines():
        p = line.split()
        if p and p[0] == 'E':
            out.append(bytes.fromhex(p[5]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    args = ap.parse_args()
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    if sha256(FROZEN_ENGINE.read_bytes()) != FROZEN_ENGINE_SHA256:
        raise SystemExit('frozen fixed-source-v3 engine changed')
    train = json.loads((OH / 'frozen' / 'sets' / 'train.json').read_text())['files']
    docs = []
    for f in train:
        raw = (LITERALS / f['path']).read_bytes()
        if sha256(raw) != f['sha256']:
            raise SystemExit('training file hash mismatch')
        docs.append(raw)
    singles = [bytes([b]) for b in sorted({b for raw in docs for b in raw})]
    list_file = work / 'train.list'
    list_file.write_text('\n'.join(str(LITERALS / f['path']) for f in train) + '\n')
    binary = work / 'engine_closed'
    subprocess.run(['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(binary), str(SRC), '-lm'],
                   check=True, cwd=HERE)
    env = os.environ.copy()
    env['FSV3_RECEIPT'] = (f'manifest={sha256((CODENET / "manifest.json").read_bytes())} split=primary pool=both '
                           f'cuts=none impl={sha256(SRC.read_bytes())} run=closure-holdout-v1')
    env.pop('FSV3_CUTS', None)
    env.pop('FSV3_GROUPS', None)
    orders, seconds = {}, {}
    for arm, mode in MODES.items():
        out = work / f'{arm}.txt'
        t0 = time.perf_counter()
        subprocess.run([str(binary), mode, 's1-whole', str(MAX_LEN), str(KMAX), '300', str(list_file), str(out)],
                       env=env, check=True)
        seconds[arm] = round(time.perf_counter() - t0, 1)
        e = chain_entries(out)
        if e[:len(singles)] != singles:
            raise SystemExit(f'{arm}: chain does not start with the training alphabet')
        orders[arm] = e[len(singles):]
    dictionaries, reproduced = {}, {}
    for cap in CAPS:
        budget = cap - len(singles) - 1
        for arm, order in orders.items():
            if len(order) < budget:
                raise SystemExit(f'{arm}: chain has {len(order)} entries, budget {budget}')
            entries = singles + order[:budget]
            dictionaries[f'{arm}-K{cap}'] = [e.hex() for e in entries]
            if arm in ('bpe', 'token'):
                header = (OH / 'frozen' / f'{arm}-K{cap}.boh').read_bytes()
                frozen_entries, _, _ = B.parse_header(header)
                same = list(frozen_entries) == entries
                reproduced[f'{arm}-K{cap}'] = same
                if not same:
                    raise SystemExit(f'{arm}-K{cap} does not reproduce the frozen objective-holdout-v1 dictionary')
    frozen = HERE / 'frozen'
    frozen.mkdir(exist_ok=True)
    blob = json.dumps({'alphabet': len(singles), 'caps': list(CAPS), 'dictionaries': dictionaries}, indent=1) + '\n'
    (frozen / 'dictionaries.json').write_text(blob)
    (frozen / 'train-summary.json').write_text(json.dumps({
        'train_files': len(docs), 'train_bytes': sum(map(len, docs)), 'alphabet': len(singles),
        'engine_seconds': seconds, 'reproduces_objective_holdout_v1': reproduced,
        'engine_closed_sha256': sha256(SRC.read_bytes()), 'frozen_engine_sha256': FROZEN_ENGINE_SHA256,
        'dictionaries_sha256': sha256(blob.encode()),
    }, indent=1) + '\n')
    print(json.dumps({'seconds': seconds, 'reproduced': reproduced, 'dictionaries_sha256': sha256(blob.encode())}))


if __name__ == '__main__':
    main()
