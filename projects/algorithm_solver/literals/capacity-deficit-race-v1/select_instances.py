#!/usr/bin/env python3
"""Select the two unseen sets of PREREGISTRATION.md from pinned public packages. Reads files only: it computes
no rank, no bound and no dictionary. Python 3.10+.

    python3 -B select_instances.py --source lodash=/path/to/node_modules/lodash --source cpython=/path/to/lib/python3.14 ...

Writes instances-a.json (texts embedded) and instances-b.json (paths, sizes and SHA-256 only). Local paths are
arguments and are never written to the outputs.

Set A, sibling-file families: per source, the directories of its subtree holding at least six files of the
source's extension between 300 and 4,000 bytes are sorted and shuffled with the seed; one family is a run of 3,
4 or 6 files that are consecutive in name order inside one directory. Families never share a file.

Set B, large directories: every file of the extension between 200 and 60,000 bytes under the named subtree,
in path order. The eight directories were named by hand from file counts and byte totals alone.
"""
import hashlib
import json
import os
import random
import sys

SEED = 'capacity-deficit-race-v1/2026-11-22'
HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'node_modules', '__pycache__', 'site-packages', 'test', 'tests'}
SEEN_CPYTHON = {'asyncio', 'multiprocessing', 'sqlite3', 'unittest'}      # used in capacity-lagrangian-race-v1
NOT_UPSTREAM = {('cpython', 'sitecustomize.py'), ('cpython', '_sysconfigdata__darwin_darwin.py')}   # added by the installer or the build; not in the pinned tag

SOURCES = {
    'cpython': {'name': 'CPython standard library', 'version': '3.14.2', 'licence': 'PSF-2.0', 'pin': 'python/cpython tag v3.14.2, directory Lib/'},
    'three': {'name': 'three', 'version': '0.186.0', 'licence': 'MIT', 'pin': 'npm three@0.186.0'},
    'rxjs': {'name': 'rxjs', 'version': '7.8.2', 'licence': 'Apache-2.0', 'pin': 'npm rxjs@7.8.2'},
    'lodash': {'name': 'lodash', 'version': '4.18.1', 'licence': 'MIT', 'pin': 'npm lodash@4.18.1'},
    'babel-runtime': {'name': '@babel/runtime', 'version': '7.28.4', 'licence': 'MIT', 'pin': 'npm @babel/runtime@7.28.4'},
    'ajv': {'name': 'ajv', 'version': '8.18.0', 'licence': 'MIT', 'pin': 'npm ajv@8.18.0'},
    'eslint': {'name': 'eslint', 'version': '9.39.2', 'licence': 'MIT', 'pin': 'npm eslint@9.39.2'},
    'zod': {'name': 'zod', 'version': '3.25.76', 'licence': 'MIT', 'pin': 'npm zod@3.25.76'},
    'caniuse-lite': {'name': 'caniuse-lite', 'version': '1.0.30001810', 'licence': 'CC-BY-4.0', 'pin': 'npm caniuse-lite@1.0.30001810'},
    'date-fns': {'name': 'date-fns', 'version': '2.30.0', 'licence': 'MIT', 'pin': 'npm date-fns@2.30.0'},
}
# Set A: (source, subtree, extension, families, directories skipped inside the subtree)
SET_A = (
    ('cpython', '', '.py', 6, SEEN_CPYTHON),
    ('three', 'src', '.js', 5, set()),
    ('rxjs', 'src', '.ts', 4, set()),
    ('lodash', '', '.js', 2, set()),
    ('babel-runtime', 'helpers', '.js', 2, {'esm'}),
    ('ajv', 'lib', '.ts', 2, set()),
    ('eslint', 'lib', '.js', 2, set()),
    ('zod', 'src', '.ts', 1, set()),
)
# Set B: (id, source, subtree, extension, recursive, directories skipped)
SET_B = (
    ('B1', 'three', 'src', '.js', True, set()),
    ('B2', 'eslint', 'lib', '.js', True, set()),
    ('B3', 'caniuse-lite', 'data', '.js', True, set()),
    ('B4', 'date-fns', 'esm/locale', '.js', True, set()),
    ('B5', 'rxjs', 'src', '.ts', True, set()),
    ('B6', 'cpython', 'encodings', '.py', False, set()),
    ('B7', 'cpython', '', '.py', False, set()),
    ('B8', 'lodash', '', '.js', True, set()),
)
A_BYTES, B_BYTES, FAMILY_SIZES = (300, 4_000), (200, 60_000), (3, 4, 6)


def check_version(source, root):
    want = SOURCES[source]['version']
    if source == 'cpython':                            # the standard library of the interpreter running this script
        import platform
        got = platform.python_version() if os.path.samefile(os.path.dirname(os.__file__), root) else 'not the running interpreter'
    else:
        got = json.load(open(os.path.join(root, 'package.json')))['version']
    if got != want:
        raise SystemExit(f'FAILED: {source} is version {got}, the pin is {want}')


def listing(source, root, subtree, extension, size_range, recursive, skip):
    """Directory (relative, '/'-separated) -> sorted list of (relative path, bytes) for files that qualify."""
    out = {}
    base = os.path.join(root, subtree) if subtree else root
    for directory, subdirs, names in os.walk(base):
        subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS and s not in skip) if recursive else []
        rel_dir = os.path.relpath(directory, root).replace(os.sep, '/')
        rel_dir = '' if rel_dir == '.' else rel_dir
        rows = []
        for name in sorted(names):
            if not name.endswith(extension) or (source, (rel_dir + '/' if rel_dir else '') + name) in NOT_UPSTREAM:
                continue
            raw = open(os.path.join(directory, name), 'rb').read()
            if not size_range[0] <= len(raw) <= size_range[1]:
                continue
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            rows.append(((rel_dir + '/' if rel_dir else '') + name, raw))
        if rows:
            out[rel_dir] = rows
    return out


def main():
    roots = dict(arg.split('=', 1) for flag, arg in zip(sys.argv[1::2], sys.argv[2::2]) if flag == '--source')
    missing = sorted(set(SOURCES) - set(roots))
    if missing:
        raise SystemExit(f'FAILED: no --source given for {missing}')
    for source, root in roots.items():
        check_version(source, root)

    families, used = [], set()
    for source, subtree, extension, count, skip in SET_A:
        rng = random.Random(f'{SEED}/A/{source}')
        dirs = {d: rows for d, rows in listing(source, roots[source], subtree, extension, A_BYTES, True, skip).items() if len(rows) >= 6}
        order = sorted(dirs)
        rng.shuffle(order)
        made, turn = 0, 0
        while made < count:
            if turn >= 50 * len(order):
                raise SystemExit(f'FAILED: {source} cannot supply {count} families')
            directory = order[turn % len(order)]
            turn += 1
            size = rng.choice(FAMILY_SIZES)
            available = [row for row in dirs[directory] if (source, row[0]) not in used]
            if len(available) < size:
                continue
            start = rng.randrange(len(available) - size + 1)
            chosen = available[start:start + size]
            if len({raw for _, raw in chosen}) < size:
                continue
            used.update((source, path) for path, _ in chosen)
            families.append({'source': source, 'directory': directory,
                             'files': [{'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for path, raw in chosen],
                             'programs': [raw.decode('utf-8') for _, raw in chosen]})
            made += 1
    corpora_a = {f'A{n + 1:02}': family for n, family in enumerate(families)}

    corpora_b = {}
    for key, source, subtree, extension, recursive, skip in SET_B:
        rows = [row for _, group in sorted(listing(source, roots[source], subtree, extension, B_BYTES, recursive, skip).items()) for row in group]
        rows.sort()
        corpora_b[key] = {'source': source, 'subtree': subtree, 'extension': extension, 'recursive': recursive,
                          'files': [{'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for path, raw in rows]}

    header = {'seed': SEED, 'sources': SOURCES}
    with open(os.path.join(HERE, 'instances-a.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(header, schema='capacity-deficit-race-a/v1', fileBytes=A_BYTES, corpora=corpora_a), f, indent=1, ensure_ascii=True)
        f.write('\n')
    with open(os.path.join(HERE, 'instances-b.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(header, schema='capacity-deficit-race-b/v1', fileBytes=B_BYTES, corpora=corpora_b), f, indent=1, ensure_ascii=True)
        f.write('\n')
    for key, c in corpora_a.items():
        print(key, c['source'], c['directory'] or '.', len(c['files']), 'files', sum(x['bytes'] for x in c['files']), 'bytes')
    for key, c in corpora_b.items():
        print(key, c['source'], c['subtree'] or '.', len(c['files']), 'files', sum(x['bytes'] for x in c['files']), 'bytes')


if __name__ == '__main__':
    main()
