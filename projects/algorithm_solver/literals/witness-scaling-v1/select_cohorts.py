#!/usr/bin/env python3
"""Select unseen scaling cohorts (40, 80, 160 programs) from two pinned public source families.

Reads files, sizes, ASCII validity and AST function spans only: computes no rank, no bound and no
dictionary. Local paths are passed as --source arguments and are never written to the output.

    python3 -B select_cohorts.py --source lodash=/path/to/lodash --source cpython=/path/to/python3.14

Families:
  - J (JavaScript utility modules): lodash@4.17.21 root .js files (excluding lodash/core bundles),
    pure ASCII, 150..2,500 bytes. Six disjoint cohorts: J-40-a, J-40-b, J-80-a, J-80-b, J-160-a, J-160-b.
  - P (Python stdlib functions): CPython 3.14.2 Lib/ top-level def functions extracted via ast.parse
    (excluding test/tests/site-packages/idlelib/tkinter/turtledemo/ensurepip/venv/lib2to3/encodings and
    previously seen packages asyncio/multiprocessing/sqlite3/unittest), pure ASCII, 150..1,500 bytes,
    deduplicated by exact bytes. Six disjoint scaling cohorts (P-40-a..P-160-b) plus two disjoint
    mechanism-contrast cohorts drawn from the remaining pool: P-80-clustered (packed into the fewest
    source modules) and P-80-diverse (one function per distinct module).
"""
import ast
import glob
import hashlib
import json
import os
import platform
import random
import sys

SEED = 'witness-scaling-v1/2026-11-22'
HERE = os.path.dirname(os.path.abspath(__file__))

SOURCES = {
    'lodash': {
        'name': 'lodash',
        'version': '4.17.21',
        'licence': 'MIT',
        'pin': 'npm lodash@4.17.21, root .js modules',
    },
    'cpython': {
        'name': 'CPython standard library',
        'version': '3.14.2',
        'licence': 'PSF-2.0',
        'pin': 'python/cpython tag v3.14.2, directory Lib/ top-level def functions',
    },
}

SKIP_PY_DIRS = {
    '__pycache__', 'site-packages', 'test', 'tests', 'idlelib', 'tkinter',
    'asyncio', 'multiprocessing', 'sqlite3', 'unittest',
    'turtledemo', 'ensurepip', 'venv', 'lib2to3', 'encodings',
}
SKIP_PY_FILES = {'sitecustomize.py', '_sysconfigdata__darwin_darwin.py'}
SKIP_JS_FILES = {'lodash.js', 'lodash.min.js', 'core.js', 'core.min.js'}


def check_version(source, root):
    want = SOURCES[source]['version']
    if source == 'cpython':
        got = platform.python_version() if os.path.samefile(os.path.dirname(os.__file__), root) else 'not running interpreter'
    else:
        got = json.load(open(os.path.join(root, 'package.json')))['version']
    if got != want:
        raise SystemExit(f'FAILED: {source} is version {got}, expected {want}')


def collect_lodash(root):
    items = []
    seen = set()
    for p in sorted(glob.glob(os.path.join(root, '*.js'))):
        name = os.path.basename(p)
        if name in SKIP_JS_FILES:
            continue
        raw = open(p, 'rb').read()
        if not (150 <= len(raw) <= 2500) or not all(b < 128 for b in raw):
            continue
        if raw in seen:
            continue
        seen.add(raw)
        items.append({
            'id': f'lodash:{name}',
            'source': 'lodash',
            'module': name,
            'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'text': raw.decode('ascii'),
        })
    return items


def collect_cpython(root):
    items = []
    seen = set()
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_PY_DIRS)
        for name in sorted(files):
            if not name.endswith('.py') or name in SKIP_PY_FILES:
                continue
            full = os.path.join(directory, name)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            try:
                text = open(full, 'r', encoding='utf-8').read()
                tree = ast.parse(text)
            except Exception:
                continue
            lines = text.splitlines(keepends=True)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.lineno and node.end_lineno:
                    src = ''.join(lines[node.lineno - 1:node.end_lineno])
                    raw = src.encode('utf-8')
                    if not (150 <= len(raw) <= 1500) or not all(b < 128 for b in raw):
                        continue
                    if raw in seen:
                        continue
                    seen.add(raw)
                    items.append({
                        'id': f'cpython:{rel}:{node.name}:{node.lineno}',
                        'source': 'cpython',
                        'module': rel,
                        'bytes': len(raw),
                        'sha256': hashlib.sha256(raw).hexdigest(),
                        'text': raw.decode('ascii'),
                    })
    return items


def main():
    roots = dict(arg.split('=', 1) for flag, arg in zip(sys.argv[1::2], sys.argv[2::2]) if flag == '--source')
    for src in ('lodash', 'cpython'):
        if src not in roots:
            raise SystemExit(f'FAILED: missing --source {src}=...')
        check_version(src, roots[src])

    j_pool = collect_lodash(roots['lodash'])
    p_pool = collect_cpython(roots['cpython'])
    if len(j_pool) < 560:
        raise SystemExit(f'FAILED: lodash pool too small ({len(j_pool)} < 560)')
    if len(p_pool) < 720:
        raise SystemExit(f'FAILED: cpython pool too small ({len(p_pool)} < 720)')

    cohorts = []

    # Family J: 6 disjoint scaling cohorts
    j_shuffled = list(j_pool)
    random.Random(f'{SEED}/J').shuffle(j_shuffled)
    cursor = 0
    for size in (40, 80, 160):
        for rep in ('a', 'b'):
            chunk = sorted(j_shuffled[cursor:cursor + size], key=lambda x: x['id'])
            cursor += size
            cohorts.append({
                'cohortId': f'J-{size}-{rep}',
                'family': 'J',
                'role': 'scaling',
                'split': 'train' if rep == 'a' else 'holdout',
                'size': size,
                'source': 'lodash',
                'programs': chunk,
            })

    # Family P: 6 disjoint scaling cohorts
    p_shuffled = list(p_pool)
    random.Random(f'{SEED}/P').shuffle(p_shuffled)
    cursor = 0
    used_p_ids = set()
    for size in (40, 80, 160):
        for rep in ('a', 'b'):
            chunk = sorted(p_shuffled[cursor:cursor + size], key=lambda x: x['id'])
            cursor += size
            used_p_ids.update(x['id'] for x in chunk)
            cohorts.append({
                'cohortId': f'P-{size}-{rep}',
                'family': 'P',
                'role': 'scaling',
                'split': 'train' if rep == 'a' else 'holdout',
                'size': size,
                'source': 'cpython',
                'programs': chunk,
            })

    # Mechanism contrast from remaining disjoint CPython pool
    rem = [x for x in p_pool if x['id'] not in used_p_ids]
    by_mod = {}
    for x in rem:
        by_mod.setdefault(x['module'], []).append(x)

    # P-80-clustered: pack from modules with the most remaining eligible functions
    clustered = []
    for mod, items in sorted(by_mod.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        for x in sorted(items, key=lambda item: item['id']):
            if len(clustered) < 80:
                clustered.append(x)
        if len(clustered) >= 80:
            break
    assert len(clustered) == 80
    clustered_ids = {x['id'] for x in clustered}
    clustered_mods = {x['module'] for x in clustered}

    # P-80-diverse: 1 function per distinct module, disjoint from main scaling cohorts and P-80-clustered
    rem_mods = sorted(m for m, items in by_mod.items() if m not in clustered_mods and any(x['id'] not in clustered_ids for x in items))
    random.Random(f'{SEED}/P-diverse').shuffle(rem_mods)
    if len(rem_mods) < 80:
        raise SystemExit(f'FAILED: only {len(rem_mods)} distinct modules left for P-80-diverse')
    diverse = []
    rng_d = random.Random(f'{SEED}/P-diverse-pick')
    for mod in sorted(rem_mods[:80]):
        cands = sorted(by_mod[mod], key=lambda item: item['id'])
        diverse.append(rng_d.choice(cands))
    assert len(diverse) == 80

    cohorts.append({
        'cohortId': 'P-80-clustered',
        'family': 'P',
        'role': 'contrast',
        'split': 'contrast',
        'size': 80,
        'source': 'cpython',
        'moduleCount': len(clustered_mods),
        'programs': sorted(clustered, key=lambda x: x['id']),
    })
    cohorts.append({
        'cohortId': 'P-80-diverse',
        'family': 'P',
        'role': 'contrast',
        'split': 'contrast',
        'size': 80,
        'source': 'cpython',
        'moduleCount': len({x['module'] for x in diverse}),
        'programs': sorted(diverse, key=lambda x: x['id']),
    })

    # Verify global disjointness across all 14 cohorts
    all_ids = [p['id'] for c in cohorts for p in c['programs']]
    assert len(all_ids) == len(set(all_ids)), 'overlap detected between cohorts'

    out = {
        'seed': SEED,
        'sources': SOURCES,
        'poolCounts': {'lodash': len(j_pool), 'cpython': len(p_pool)},
        'cohorts': cohorts,
    }
    out_path = os.path.join(HERE, 'cohorts.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    h = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    print(f'Wrote {out_path} ({os.path.getsize(out_path):,} bytes, sha256={h})')
    for c in cohorts:
        mods = len({p['module'] for p in c['programs']})
        tot_b = sum(p['bytes'] for p in c['programs'])
        print(f"  {c['cohortId']:15s}  n={c['size']:3d}  modules={mods:3d}  total_bytes={tot_b:7,d}")


if __name__ == '__main__':
    main()
