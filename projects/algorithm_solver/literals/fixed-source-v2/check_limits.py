#!/usr/bin/env python3
"""Policy-matched census and no-singleton reachability, from the sources alone.

Reachability ignores K and B: it says whether a file has any parse into entries
the policy allows. It says nothing about one fixed-budget dictionary.

    check_limits.py census <private folder> <output json>
    check_limits.py reach  <private folder> <output json>
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / 'fixed-source-v1' / 'manifest.json'
LENGTHS = (2, 4, 8, 16, 32, 64)
GRID_L = (1, 2, 4, 8, 16, 32, 64)
POLICIES = ('s1-whole', 's1-nowhole', 's2-nowhole')


def corpora(private):
    rows = json.loads(MANIFEST.read_text())['problems']
    files = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (Path(private) / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit('hash mismatch')
            docs.append(raw)
        files[language] = docs
    files['both'] = files['python'] + files['javascript']
    return files


def census(files):
    """Which multibyte whole-file strings each maximum length makes eligible."""
    out = {}
    for name, docs in files.items():
        whole = set(docs)
        out[name] = {'files': len(docs), 'distinct_files': len(whole), 'bytes': sum(map(len, docs)),
                     'minimum_file_bytes': min(map(len, docs)), 'by_L': {}}
        for limit in GRID_L:
            count = sum(1 for raw in whole if 2 <= len(raw) <= limit)
            out[name]['by_L'][str(limit)] = {'whole_file_strings_within_L': count,
                                             'isolation_identical_to_primary': count == 0}
    return out


def shared_strings(docs, limit):
    """Strings of 2..limit bytes in at least two files, not a whole file."""
    whole = set(docs)
    allowed, alive = set(), None
    for length in range(2, limit + 1):
        owner, shared = {}, set()
        for index, raw in enumerate(docs):
            for at in range(len(raw) - length + 1):
                if alive is not None and (index, at) not in alive:
                    continue
                piece = raw[at:at + length]
                mark = owner.get(piece)
                if mark is None:
                    owner[piece] = index
                elif mark != index:
                    shared.add(piece)
        allowed |= {s for s in shared if s not in whole}
        alive = {(index, at) for index, raw in enumerate(docs)
                 for at in range(len(raw) - length + 1) if raw[at:at + length] in shared}
        if not shared:
            break
    return allowed


def reachable(raw, limit, policy, whole, sizes, allowed):
    size = len(raw)
    can = bytearray(size + 1)
    can[0] = 1
    for start in range(size):
        if not can[start]:
            continue
        for length in range(2, min(limit, size - start) + 1):
            if policy == 's2-nowhole':
                legal = raw[start:start + length] in allowed
            elif policy == 's1-nowhole':
                legal = length not in sizes or raw[start:start + length] not in whole
            else:
                legal = True
            if legal:
                can[start + length] = 1
    return bool(can[size])


def identity(raw, limit):
    """The closed form for the primary policy, with K and B ignored."""
    if len(raw) < 2:
        return False
    return len(raw) % 2 == 0 if limit == 2 else True


def reach(files):
    out = {}
    for name, docs in files.items():
        whole, sizes = set(docs), set(map(len, docs))
        out[name] = {}
        for policy in POLICIES:
            out[name][policy] = {}
            for limit in LENGTHS:
                allowed = shared_strings(docs, limit) if policy == 's2-nowhole' else None
                flags = [reachable(raw, limit, policy, whole, sizes, allowed) for raw in docs]
                if policy == 's1-whole':
                    for raw, flag in zip(docs, flags):
                        if flag != identity(raw, limit):
                            raise SystemExit(f'reachability identity failed at L={limit}')
                out[name][policy][str(limit)] = {'reachable_files': sum(flags),
                                                 'proved_unreachable': len(docs) - sum(flags)}
            print(name, policy, {k: v['reachable_files'] for k, v in out[name][policy].items()}, flush=True)
    return out


def main():
    action, private, output = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    files = corpora(private)
    if action == 'census':
        result = {'schema': 'gamma.fixed-source-census.v2', 'corpora': census(files)}
    elif action == 'reach':
        result = {'schema': 'gamma.fixed-source-reachability.v2', 'corpora': reach(files)}
    else:
        raise SystemExit('unknown action')
    output.write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
