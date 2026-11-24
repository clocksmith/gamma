#!/usr/bin/env python3
"""Independent checker for fixed-source-v3. Shares no code with engine.c.

Each chain's receipt must bind its scenario. The checker recounts support by file
or by problem, honors lexer cuts, parses every file at every scored prefix and
compares the joined pieces with the manifest bytes. Writes source-free aggregates.

    verify.py <v1 private folder> <side folder> <run folder> <output json> <run id> <impl sha> [workers]
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
GRID_B = [1024, 2048, 4096, 8192, 16384, 32768, 65536, None]
CHAIN_ARMS = ['greedy-entry', 'greedy-byte', 'greedtok', 'freq-occ', 'freq-doc', 'bpe', 'pathpiece']
SINGLE_ARMS = ['lp-det', 'lp-bias']
POLICIES = {'s1-whole': (1, True, 'file'), 's2-nowhole': (2, False, 'file'), 'p2-nowhole': (2, False, 'problem')}
SCENARIOS = {'s1-whole': ('s1-whole', False), 's2-nowhole': ('s2-nowhole', False),
             'p2-nowhole': ('p2-nowhole', False), 's1-whole-cuts': ('s1-whole', True)}
RECEIPT_KEYS = {'policy', 'mode', 'L', 'K', 'limit', 'manifest', 'pool', 'cuts', 'impl', 'run'}
TERMINAL = -1
CORPUS, VIEWS, BINDING = {}, {}, {}


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


def split_segments(docs, cuts):
    """Cuts one byte-map across the corpus into per-file segments."""
    if len(cuts) != sum(map(len, docs)):
        raise SystemExit('cut map length differs from the corpus')
    out, offset = [], 0
    for raw in docs:
        marks = cuts[offset:offset + len(raw)]
        if marks[:1] == b'\1':
            raise SystemExit('a cut at the start of a file')
        pieces, start = [], 0
        for at in range(1, len(raw)):
            if marks[at]:
                pieces.append(raw[start:at])
                start = at
        pieces.append(raw[start:])
        out.append(pieces)
        offset += len(raw)
    return out


def build_views(docs, groups, cuts, use_cuts, policy):
    segments = split_segments(docs, cuts) if use_cuts else [[raw] for raw in docs]
    unit = POLICIES[policy][2]
    keys = groups if unit == 'problem' else list(range(len(docs)))
    units = {}
    for key, parts in zip(keys, segments):
        units.setdefault(key, []).extend(parts)
    return segments, list(units.values())


def read_chain(path):
    receipt, entries, merges, reach, done, seed = None, [], [], None, None, None
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
        elif kind == 'S':
            seed = tuple(int(x) for x in line.split(' ')[1:])
        elif kind == 'D':
            done = dict(item.split('=') for item in line.split(' ')[2:])
    if receipt is None:
        raise Rejected('no receipt')
    if done is None:
        raise Rejected('unfinished chain')
    return receipt, entries, merges, reach, done, seed


def check_receipt(receipt, scenario, mode, limit, corpus, budget, binding):
    policy, use_cuts = SCENARIOS[scenario]
    wanted = {'policy': policy, 'mode': mode, 'L': str(limit), 'pool': corpus, 'manifest': binding['manifest'],
              'impl': binding['impl'], 'run': binding['run'], 'cuts': binding['cuts'][corpus] if use_cuts else 'none'}
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


def support(entry, units):
    """Distinct support units holding entry, counted up to two."""
    count = 0
    for parts in units:
        if any(entry in part for part in parts):
            count += 1
            if count == 2:
                break
    return count


def check_entries(entries, docs, units, limit, policy, singles_allowed=True):
    if policy not in POLICIES:
        raise Rejected('unknown policy')
    least, whole_allowed, _ = POLICIES[policy]
    whole, seen, one_unit, whole_entries = set(docs), set(), set(), set()
    for row in entries:
        entry = row[4]
        if entry in seen:
            raise Rejected('duplicate entry')
        seen.add(entry)
        if not entry or len(entry) > limit:
            raise Rejected('entry length outside the rule')
        count = support(entry, units)
        if count == 0:
            raise Rejected('entry is absent from the pool')
        if len(entry) == 1:
            if not singles_allowed:
                raise Rejected('single character in a no-singleton chain')
            continue
        if count < least:
            raise Rejected('entry has too little support')
        if entry in whole:
            if not whole_allowed:
                raise Rejected('entry equals a whole file')
            whole_entries.add(entry)
        if count == 1:
            one_unit.add(entry)
    return one_unit, whole_entries


def insert(root, entry):
    node = root
    for byte in entry:
        node = node.setdefault(byte, {})
    node[TERMINAL] = entry


def parse(raw, root):
    size = len(raw)
    missing = size + 1
    best, back = [missing] * (size + 1), [None] * (size + 1)
    best[0] = 0
    for start in range(size):
        cost = best[start]
        if cost == missing:
            continue
        node, at = root, start
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


def score(docs, segments, root):
    spelled = tokens = 0
    for raw, parts in zip(docs, segments):
        out = []
        for part in parts:
            pieces = parse(part, root)
            if pieces is None:
                out = None
                break
            out += pieces
        if out is None:
            continue
        if b''.join(out) != raw:
            raise Rejected('a parse did not reconstruct its file')
        spelled += 1
        tokens += len(out)
    return spelled, tokens


def ordinary_bpe(docs, entries, merges, wanted):
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
        pair, merged = token(left) + token(right), token(left + right)
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
    scenario, corpus, limit, arm, folder = job
    path = Path(folder) / scenario / f'{corpus}-L{limit}-{arm}.txt'
    policy = SCENARIOS[scenario][0]
    docs = CORPUS[corpus]
    segments, units = VIEWS[(scenario, corpus)]
    try:
        receipt, entries, merges, _, done, _ = read_chain(path)
        check_receipt(receipt, scenario, arm, limit, corpus, None, BINDING)
        check_framing(entries)
        one_unit, whole_entries = check_entries(entries, docs, units, limit, policy)
        wanted = sorted({prefix_for(entries, k, b) for k in GRID_K for b in GRID_B})
        root, results, at = {}, {}, 0
        for size in wanted:
            while at < size:
                insert(root, entries[at][4])
                at += 1
            results[size] = score(docs, segments, root) if size else (0, 0)
        ordinary = ordinary_bpe(docs, entries, merges, wanted) if arm == 'bpe' else {}
        rows = []
        for k in GRID_K:
            for b in GRID_B:
                size = prefix_for(entries, k, b)
                spelled, tokens = results[size]
                head = [row[4] for row in entries[:size]]
                row = {'scenario': scenario, 'policy': policy, 'corpus': corpus, 'L': limit, 'arm': arm, 'K': k, 'B': b,
                       'entries': size, 'stored_bytes': entries[size - 1][1] if size else 0, 'files': len(docs),
                       'spelled': spelled, 'emissions': tokens if spelled == len(docs) else None,
                       'one_unit_entries': sum(e in one_unit for e in head),
                       'whole_file_entries': sum(e in whole_entries for e in head), 'verified': True}
                if arm == 'bpe' and size:
                    row['ordinary_emissions'] = ordinary.get(size) if spelled == len(docs) else None
                if size and spelled == len(docs) and arm not in ('bpe', 'pathpiece') and entries[size - 1][2] != tokens:
                    raise Rejected(f'engine says {entries[size - 1][2]}, parse says {tokens} at {size}')
                rows.append(row)
    except Rejected as error:
        raise SystemExit(f'{path}: {error}') from error
    return {'scenario': scenario, 'corpus': corpus, 'L': limit, 'arm': arm, 'rows': rows,
            'chain': [(e[0], e[1], e[2]) for e in entries], 'stopped': int(done.get('stopped', 0)),
            'candidates': int(done.get('candidates', 0)), 'seconds': float(done.get('seconds', 0)),
            'maxrss_kb': int(done.get('maxrss_kb', 0))}


def check_single(job):
    scenario, corpus, limit, arm, budget, folder = job
    path = Path(folder) / scenario / f'{corpus}-L{limit}-{arm}-K{budget}.txt'
    policy = SCENARIOS[scenario][0]
    docs = CORPUS[corpus]
    segments, units = VIEWS[(scenario, corpus)]
    try:
        receipt, entries, _, _, done, _ = read_chain(path)
        check_receipt(receipt, scenario, arm, limit, corpus, budget, BINDING)
        if len(entries) > budget:
            raise Rejected('dictionary over its entry budget')
        check_framing(entries)
        check_entries(entries, docs, units, limit, policy)
        root = {}
        for row in entries:
            insert(root, row[4])
        spelled, tokens = score(docs, segments, root)
        if spelled != len(docs):
            raise Rejected('a dictionary did not spell every file')
        row = {'scenario': scenario, 'policy': policy, 'corpus': corpus, 'L': limit, 'arm': arm, 'K': budget, 'B': None,
               'entries': len(entries), 'stored_bytes': entries[-1][1], 'files': len(docs), 'spelled': spelled,
               'emissions': tokens, 'verified': True}
    except Rejected as error:
        raise SystemExit(f'{path}: {error}') from error
    row['seconds'] = float(done.get('seconds', 0))
    return row


def main():
    private, side, run, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    workers = int(sys.argv[7]) if len(sys.argv) > 7 else 12
    CORPUS.update(load_corpus(private))
    BINDING.update({'manifest': sha256_file(MANIFEST), 'run': sys.argv[5], 'impl': sys.argv[6],
                    'cuts': {c: sha256_file(side / f'{c}.cuts') for c in CORPUS}})
    for scenario, (policy, use_cuts) in SCENARIOS.items():
        for corpus, docs in CORPUS.items():
            groups = [int(x) for x in (side / f'{corpus}.groups').read_text().split()]
            cuts = (side / f'{corpus}.cuts').read_bytes() if use_cuts else b''
            VIEWS[(scenario, corpus)] = build_views(docs, groups, cuts, use_cuts, policy)
    folder = run / 'chains'
    chain_jobs, single_jobs = [], []
    for scenario in SCENARIOS:
        for path in sorted((folder / scenario).glob('*.txt')):
            corpus, rest = path.stem.split('-L', 1)
            limit, arm = rest.split('-', 1)
            if arm in CHAIN_ARMS:
                chain_jobs.append((scenario, corpus, int(limit), arm, str(folder)))
            else:
                name, budget = arm.rsplit('-K', 1)
                if name not in SINGLE_ARMS:
                    raise SystemExit(f'unknown chain: {path.name}')
                single_jobs.append((scenario, corpus, int(limit), name, int(budget), str(folder)))
    os.nice(19)
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        checked = pool.map(check_chain, chain_jobs, chunksize=1)
        singles = pool.map(check_single, single_jobs, chunksize=1) if single_jobs else []
    key = lambda c: f"{c['scenario']}/{c['corpus']}-L{c['L']}-{c['arm']}"
    summary = {'schema': 'gamma.fixed-source-verification.v3', 'run': BINDING['run'], 'impl': BINDING['impl'],
               'manifest': BINDING['manifest'], 'cuts': BINDING['cuts'], 'chains': len(checked),
               'single_dictionaries': len(singles), 'stopped_chains': [key(c) for c in checked if c['stopped']],
               'chain_meta': {key(c): {'candidates': c['candidates'], 'seconds': c['seconds'], 'maxrss_kb': c['maxrss_kb']}
                              for c in checked},
               'rows': [row for item in checked for row in item['rows']], 'singles': singles}
    output.write_text(json.dumps(summary, separators=(',', ':')) + '\n')
    (output.parent / 'chains.json').write_text(json.dumps({key(c): c['chain'] for c in checked}, separators=(',', ':')))
    print(f"verified {len(checked)} chains, {len(summary['rows'])} cells, {len(singles)} single dictionaries, "
          f"stopped {len(summary['stopped_chains'])}")


if __name__ == '__main__':
    main()
