#!/usr/bin/env python3
"""Independent checker for fixed-source-v2. Shares no code with engine.c.

Reads each private chain, rejects a missing or conflicting receipt, recounts
file support, enforces the policy, parses every file at every scored prefix and
compares the joined pieces with the manifest bytes. Writes source-free aggregates.

    verify.py <private folder> <run folder> <output json> <run id> <impl sha> [workers]
"""
import hashlib
import json
import multiprocessing
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / 'fixed-source-v1' / 'manifest.json'
GRID_K = [64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096]
GRID_L = [1, 2, 4, 8, 16, 32, 64]
GRID_B = [1024, 2048, 4096, 8192, 16384, 32768, 65536, None]
ARMS = ['greedy-entry', 'greedy-byte', 'freq-occ', 'freq-doc', 'bpe', 'cover-mixed', 'cover-nosingle']
POLICIES = {'s1-whole': (1, True), 's1-nowhole': (1, False), 's2-nowhole': (2, False)}
RECEIPT_KEYS = {'policy', 'mode', 'L', 'K', 'limit', 'manifest', 'pool', 'impl', 'run'}
TERMINAL = -1
CORPUS = {}
BINDING = {}


class Rejected(Exception):
    """A chain broke a rule of the frozen design."""


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_corpus(private, manifest=MANIFEST):
    rows = json.loads(Path(manifest).read_text())['problems']
    files = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (Path(private) / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit(f'hash mismatch: {language} {row["id"]}')
            docs.append(raw)
        files[language] = docs
    files['both'] = files['python'] + files['javascript']
    return files


def read_chain(path):
    receipt, entries, merges, reach, done = None, [], [], None, None
    for line in Path(path).read_text().splitlines():
        kind = line[0]
        if kind == 'H':
            if receipt is not None:
                raise Rejected('two receipts')
            pairs = [item.split('=', 1) for item in line.split(' ')[1:]]
            receipt = dict(pairs)
            if len(receipt) != len(pairs) or set(receipt) != RECEIPT_KEYS:
                raise Rejected('receipt fields are missing or conflict')
        elif kind == 'E':
            _, k, stored, tokens, spelled, value = line.split(' ')
            entries.append((int(k), int(stored), int(tokens), int(spelled), bytes.fromhex(value)))
        elif kind == 'M':
            _, left, right = line.split(' ')
            merges.append((len(entries), bytes.fromhex(left), bytes.fromhex(right)))
        elif kind == 'R':
            reach = tuple(int(x) for x in line.split(' ')[1:])
        elif kind == 'D':
            done = dict(item.split('=') for item in line.split(' ')[2:])
    if receipt is None:
        raise Rejected('no receipt')
    if done is None:
        raise Rejected('unfinished chain')
    return receipt, entries, merges, reach, done


def check_receipt(receipt, policy, mode, limit, corpus, budget, binding):
    wanted = {'policy': policy, 'mode': mode, 'L': str(limit), 'pool': corpus,
              'manifest': binding['manifest'], 'impl': binding['impl'], 'run': binding['run']}
    if budget is not None:
        wanted['K'] = str(budget)
    for key, value in wanted.items():
        if receipt.get(key) != value:
            raise Rejected(f'receipt {key} is {receipt.get(key)!r}, expected {value!r}')


def check_framing(entries):
    stored = 0
    for index, row in enumerate(entries):
        stored += 1 + len(row[4])
        if row[0] != index + 1:
            raise Rejected('entry counter out of order')
        if row[1] != stored:
            raise Rejected('stored bytes differ at a prefix')


def support(entry, docs):
    """Distinct files holding entry, counted up to two."""
    count = 0
    for raw in docs:
        if entry in raw:
            count += 1
            if count == 2:
                break
    return count


def check_entries(entries, docs, limit, policy, singles_allowed):
    """Enforces the policy. Returns entries seen in one file, and whole-file entries."""
    if policy not in POLICIES:
        raise Rejected('unknown policy')
    least, whole_allowed = POLICIES[policy]
    whole = set(docs)
    seen, one_file, whole_entries = set(), set(), set()
    for row in entries:
        entry = row[4]
        if entry in seen:
            raise Rejected('duplicate entry')
        seen.add(entry)
        if not entry or len(entry) > limit:
            raise Rejected('entry length outside the rule')
        files = support(entry, docs)
        if files == 0:
            raise Rejected('entry is absent from the pool')
        if len(entry) == 1:
            if not singles_allowed:
                raise Rejected('single character in a no-singleton chain')
            continue
        if files < least:
            raise Rejected('entry has too little file support')
        if entry in whole:
            if not whole_allowed:
                raise Rejected('entry equals a whole file')
            whole_entries.add(entry)
        if files == 1:
            one_file.add(entry)
    return one_file, whole_entries


def insert(root, entry):
    node = root
    for byte in entry:
        node = node.setdefault(byte, {})
    node[TERMINAL] = entry


def parse(raw, root):
    """The fewest entries that spell raw, and the pieces, or None."""
    size = len(raw)
    missing = size + 1
    best = [missing] * (size + 1)
    back = [None] * (size + 1)
    best[0] = 0
    for start in range(size):
        cost = best[start]
        if cost == missing:
            continue
        node = root
        at = start
        while at < size:
            node = node.get(raw[at])
            if node is None:
                break
            at += 1
            if TERMINAL in node and cost + 1 < best[at]:
                best[at] = cost + 1
                back[at] = node[TERMINAL]
    if best[size] == missing:
        return None
    pieces, at = [], size
    while at:
        piece = back[at]
        pieces.append(piece)
        at -= len(piece)
    pieces.reverse()
    return pieces


def score(docs, root, one_file=frozenset(), whole_entries=frozenset()):
    spelled = tokens = one_file_tokens = whole_tokens = 0
    for raw in docs:
        pieces = parse(raw, root)
        if pieces is None:
            continue
        joined = b''.join(pieces)
        if joined != raw or hashlib.sha256(joined).digest() != hashlib.sha256(raw).digest():
            raise Rejected('a parse did not reconstruct its file')
        spelled += 1
        tokens += len(pieces)
        one_file_tokens += sum(piece in one_file for piece in pieces)
        whole_tokens += sum(piece in whole_entries for piece in pieces)
    return spelled, tokens, one_file_tokens, whole_tokens


def ordinary_bpe(docs, entries, merges, wanted):
    """Replays the merges with str.replace: left to right, non-overlapping."""
    ids = {}

    def token(value):
        if value not in ids:
            code = len(ids) + 0x100
            ids[value] = chr(code if code < 0xD800 else code + 0x800)
        return ids[value]

    streams = [''.join(token(bytes([b])) for b in raw) for raw in docs]
    out, pending, place = {}, sorted(set(wanted)), 0

    def record(prefix):
        nonlocal place
        while place < len(pending) and pending[place] <= prefix:
            out[pending[place]] = sum(len(s) for s in streams)
            place += 1

    for added, left, right in merges:
        if added < len(entries) and entries[added][4] == left + right:
            record(added)
        pair = token(left) + token(right)
        merged = token(left + right)
        streams = [s.replace(pair, merged) if pair in s else s for s in streams]
    while place < len(pending):
        out[pending[place]] = sum(len(s) for s in streams)
        place += 1
    return out


def prefix_for(entries, entry_cap, byte_cap):
    size = 0
    for k, stored, *_ in entries:
        if k > entry_cap or (byte_cap is not None and stored > byte_cap):
            break
        size = k
    return size


def check_chain(job):
    policy, corpus, limit, arm, folder = job
    path = Path(folder) / policy / f'{corpus}-L{limit}-{arm}.txt'
    docs = CORPUS[corpus]
    try:
        receipt, entries, merges, reach, done = read_chain(path)
        check_receipt(receipt, policy, arm, limit, corpus, None, BINDING)
        check_framing(entries)
        one_file, whole_entries = check_entries(entries, docs, limit, policy, arm != 'cover-nosingle')
        wanted = sorted({prefix_for(entries, k, b) for k in GRID_K for b in GRID_B})
        root, results, at = {}, {}, 0
        for size in wanted:
            while at < size:
                insert(root, entries[at][4])
                at += 1
            results[size] = score(docs, root, one_file, whole_entries) if size else (0, 0, 0, 0)
        ordinary = ordinary_bpe(docs, entries, merges, wanted) if arm == 'bpe' else {}
        rows = []
        for k in GRID_K:
            for b in GRID_B:
                size = prefix_for(entries, k, b)
                spelled, tokens, one_tokens, whole_tokens = results[size]
                head = [row[4] for row in entries[:size]]
                row = {'policy': policy, 'corpus': corpus, 'L': limit, 'arm': arm, 'K': k, 'B': b,
                       'entries': size, 'stored_bytes': entries[size - 1][1] if size else 0,
                       'files': len(docs), 'spelled': spelled,
                       'emissions': tokens if spelled == len(docs) else None,
                       'emissions_on_spelled': tokens,
                       'one_file_entries': sum(e in one_file for e in head),
                       'whole_file_entries': sum(e in whole_entries for e in head),
                       'one_file_tokens': one_tokens, 'whole_file_tokens': whole_tokens, 'verified': True}
                if arm == 'bpe' and size:
                    row['ordinary_emissions'] = ordinary.get(size) if spelled == len(docs) else None
                if size and spelled == len(docs) and arm.startswith(('greedy', 'freq')):
                    if entries[size - 1][2] != tokens:
                        raise Rejected(f'engine says {entries[size - 1][2]}, parse says {tokens} at {size}')
                rows.append(row)
    except Rejected as error:
        raise SystemExit(f'{path}: {error}') from error
    return {'policy': policy, 'corpus': corpus, 'L': limit, 'arm': arm, 'rows': rows,
            'chain': [(e[0], e[1], e[2]) for e in entries], 'reachable': reach,
            'stopped': int(done.get('stopped', 0)), 'candidates': int(done.get('candidates', 0)),
            'seconds': float(done.get('seconds', 0)), 'enumerate_seconds': float(done.get('enumerate_seconds', 0)),
            'maxrss_kb': int(done.get('maxrss_kb', 0))}


def check_polish(job):
    policy, corpus, limit, budget, folder = job
    path = Path(folder) / policy / f'{corpus}-L{limit}-polish-K{budget}.txt'
    docs = CORPUS[corpus]
    try:
        receipt, entries, _, _, done = read_chain(path)
        check_receipt(receipt, policy, 'polish', limit, corpus, budget, BINDING)
        if len(entries) > budget:
            raise Rejected('polished dictionary over its entry budget')
        check_framing(entries)
        one_file, whole_entries = check_entries(entries, docs, limit, policy, True)
        root = {}
        for row in entries:
            insert(root, row[4])
        spelled, tokens, one_tokens, whole_tokens = score(docs, root, one_file, whole_entries)
        if spelled != len(docs) or entries[-1][2] != tokens:
            raise Rejected(f'engine {entries[-1][2]}, parse {tokens}, spelled {spelled}')
    except Rejected as error:
        raise SystemExit(f'{path}: {error}') from error
    stored = entries[-1][1]
    return {'rows': [{'policy': policy, 'corpus': corpus, 'L': limit, 'arm': 'greedy-polish', 'K': budget, 'B': b,
                      'entries': len(entries), 'stored_bytes': stored, 'files': len(docs), 'spelled': spelled,
                      'emissions': tokens, 'emissions_on_spelled': tokens, 'one_file_entries': len(one_file),
                      'whole_file_entries': len(whole_entries), 'one_file_tokens': one_tokens,
                      'whole_file_tokens': whole_tokens, 'verified': True}
                     for b in GRID_B if b is None or stored <= b],
            'seconds': float(done.get('seconds', 0)), 'maxrss_kb': int(done.get('maxrss_kb', 0))}


def main():
    private, run, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    BINDING.update({'manifest': sha256_file(MANIFEST), 'run': sys.argv[4], 'impl': sys.argv[5]})
    workers = int(sys.argv[6]) if len(sys.argv) > 6 else 8
    CORPUS.update(load_corpus(private))
    folder = run / 'chains'
    jobs = [(policy, corpus, limit, arm, str(folder)) for policy in POLICIES
            for corpus in ('python', 'javascript', 'both') for limit in GRID_L for arm in ARMS
            if (folder / policy / f'{corpus}-L{limit}-{arm}.txt').exists()]
    polish = []
    for policy in POLICIES:
        for path in sorted((folder / policy).glob('*-polish-K*.txt')):
            corpus, rest = path.stem.split('-L', 1)
            limit, tail = rest.split('-polish-K')
            polish.append((policy, corpus, int(limit), int(tail), str(folder)))
    os.nice(19)
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        checked = pool.map(check_chain, jobs, chunksize=1)
        polished = pool.map(check_polish, polish, chunksize=1) if polish else []
    rows = [row for item in checked for row in item['rows']] + [row for item in polished for row in item['rows']]
    key = lambda c: f"{c['policy']}/{c['corpus']}-L{c['L']}-{c['arm']}"
    summary = {'schema': 'gamma.fixed-source-verification.v2', 'run': BINDING['run'], 'impl': BINDING['impl'],
               'manifest': BINDING['manifest'], 'chains': len(checked), 'cells': len(rows),
               'polished_dictionaries': len(polish),
               'stopped_chains': [key(c) for c in checked if c['stopped']],
               'reachability': {key(c): c['reachable'] for c in checked if c['reachable']},
               'chain_meta': {key(c): {'candidates': c['candidates'], 'seconds': c['seconds'],
                                       'enumerate_seconds': c['enumerate_seconds'], 'maxrss_kb': c['maxrss_kb']}
                              for c in checked},
               'rows': rows}
    output.write_text(json.dumps(summary, separators=(',', ':')) + '\n')
    (output.parent / 'chains.json').write_text(json.dumps({key(c): c['chain'] for c in checked}, separators=(',', ':')))
    print(f"verified {len(checked)} chains, {len(rows)} cells, {len(polish)} polished dictionaries, "
          f"stopped {len(summary['stopped_chains'])}")


if __name__ == '__main__':
    main()
