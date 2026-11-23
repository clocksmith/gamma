#!/usr/bin/env python3
"""Independent checker for fixed-source-v1. Shares no code with engine.c.

Reads every private chain, rebuilds each dictionary at every grid budget, parses
every file with its own shortest-path parser, joins the pieces and compares them
with the manifest hash. Writes source-free aggregates only.

    verify.py <private folder> <run folder> <output json> [workers]
"""
import hashlib
import json
import multiprocessing
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRID_K = [64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096]
GRID_L = [1, 2, 4, 8, 16, 32, 64]
GRID_B = [1024, 2048, 4096, 8192, 16384, 32768, 65536, None]
ARMS = ['greedy-entry', 'greedy-byte', 'freq-occ', 'freq-doc', 'bpe', 'bpe-free',
        'cover-mixed', 'cover-nosingle']
TERMINAL = -1
CORPUS = {}


def load_corpus(private, manifest):
    rows = json.loads(manifest.read_text())['problems']
    files = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (private / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit(f'hash mismatch: {language} {row["id"]}')
            docs.append(raw)
        files[language] = docs
    files['both'] = files['python'] + files['javascript']
    return files


def read_chain(path):
    entries, merges, reach, done = [], [], None, None
    for line in path.read_text().splitlines():
        kind = line[0]
        if kind == 'E':
            _, k, stored, tokens, spelled, value = line.split(' ')
            entries.append((int(k), int(stored), int(tokens), int(spelled), bytes.fromhex(value)))
        elif kind == 'M':
            _, left, right = line.split(' ')
            merges.append((len(entries), bytes.fromhex(left), bytes.fromhex(right)))
        elif kind == 'R':
            reach = tuple(int(x) for x in line.split(' ')[1:])
        elif kind == 'P':
            continue
        elif kind == 'D':
            done = dict(item.split('=') for item in line.split(' ')[2:])
    if done is None:
        raise SystemExit(f'unfinished chain: {path}')
    return entries, merges, reach, done


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
    pieces = []
    at = size
    while at:
        piece = back[at]
        pieces.append(piece)
        at -= len(piece)
    pieces.reverse()
    return pieces


def score(docs, root):
    spelled, tokens = 0, 0
    for raw in docs:
        pieces = parse(raw, root)
        if pieces is None:
            continue
        joined = b''.join(pieces)
        if joined != raw or hashlib.sha256(joined).digest() != hashlib.sha256(raw).digest():
            raise SystemExit('a parse did not reconstruct its file')
        spelled += 1
        tokens += len(pieces)
    return spelled, tokens


def check_entries(entries, docs, limit, need_two_files, singles_allowed):
    whole = set(docs)
    seen = set()
    for _, _, _, _, entry in entries:
        if entry in seen:
            raise SystemExit('duplicate entry')
        seen.add(entry)
        if not entry or len(entry) > limit:
            raise SystemExit('entry length outside the rule')
        if len(entry) == 1:
            if not singles_allowed:
                raise SystemExit('single character in a no-singleton chain')
            continue
        if need_two_files:
            if entry in whole:
                raise SystemExit('entry equals a whole file')
            count = 0
            for raw in docs:
                if entry in raw:
                    count += 1
                    if count == 2:
                        break
            if count < 2:
                raise SystemExit('entry occurs in fewer than two files')


def ordinary_bpe(docs, entries, merges, wanted):
    """Replays the merges with str.replace: left to right, non-overlapping."""
    ids = {}
    def token(value):
        if value not in ids:
            code = len(ids) + 0x100
            ids[value] = chr(code if code < 0xD800 else code + 0x800)
        return ids[value]
    streams = [''.join(token(bytes([b])) for b in raw) for raw in docs]
    out = {}
    pending = sorted(set(wanted))
    place = 0
    def record(prefix):
        nonlocal place
        while place < len(pending) and pending[place] <= prefix:
            out[pending[place]] = sum(len(s) for s in streams)
            place += 1
    for added, left, right in merges:
        # A merge that creates a new entry moves the dictionary from added to added + 1.
        grows = added < len(entries) and entries[added][4] == left + right
        if grows:
            record(added)
        a, b, m = token(left), token(right), token(left + right)
        pair = a + b
        streams = [s.replace(pair, m) if pair in s else s for s in streams]
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
    corpus, limit, arm, folder = job
    path = Path(folder) / f'{corpus}-L{limit}-{arm}.txt'
    docs = CORPUS[corpus]
    entries, merges, reach, done = read_chain(path)
    check_entries(entries, docs, limit, arm != 'bpe-free', arm != 'cover-nosingle')
    for index, row in enumerate(entries):
        if row[0] != index + 1:
            raise SystemExit('entry counter out of order')
        stored = sum(1 + len(x[4]) for x in entries[:index + 1]) if index < 3 else None
        if stored is not None and stored != row[1]:
            raise SystemExit('stored bytes differ')
    if entries and entries[-1][1] != sum(1 + len(x[4]) for x in entries):
        raise SystemExit('stored bytes differ')
    wanted = sorted({prefix_for(entries, k, b) for k in GRID_K for b in GRID_B})
    root, results, at = {}, {}, 0
    for size in wanted:
        while at < size:
            insert(root, entries[at][4])
            at += 1
        results[size] = score(docs, root) if size else (0, 0)
    ordinary = ordinary_bpe(docs, entries, merges, wanted) if arm.startswith('bpe') else {}
    rows = []
    for k in GRID_K:
        for b in GRID_B:
            size = prefix_for(entries, k, b)
            spelled, tokens = results[size]
            stored = entries[size - 1][1] if size else 0
            row = {'corpus': corpus, 'L': limit, 'arm': arm, 'K': k, 'B': b, 'entries': size,
                   'stored_bytes': stored, 'files': len(docs), 'spelled': spelled,
                   'emissions': tokens if spelled == len(docs) else None,
                   'emissions_on_spelled': tokens, 'verified': True}
            if arm.startswith('bpe') and size:
                row['ordinary_emissions'] = ordinary.get(size) if spelled == len(docs) else None
            if size and spelled == len(docs) and arm.startswith(('greedy', 'freq')):
                reported = entries[size - 1][2]
                if reported != tokens:
                    raise SystemExit(f'{path.name}: engine says {reported}, parse says {tokens} at {size}')
            rows.append(row)
    chain = [(e[0], e[1], e[2]) for e in entries]
    return {'corpus': corpus, 'L': limit, 'arm': arm, 'rows': rows, 'chain': chain,
            'reachable': reach, 'stopped': int(done.get('stopped', 0)),
            'candidates': int(done.get('candidates', 0)), 'seconds': float(done.get('seconds', 0))}


def check_polish(job):
    corpus, limit, budget, folder = job
    path = Path(folder) / f'{corpus}-L{limit}-polish-K{budget}.txt'
    docs = CORPUS[corpus]
    entries, _, _, _ = read_chain(path)
    if len(entries) > budget:
        raise SystemExit('polished dictionary over its entry budget')
    check_entries(entries, docs, limit, True, True)
    root = {}
    for row in entries:
        insert(root, row[4])
    spelled, tokens = score(docs, root)
    if spelled != len(docs) or entries[-1][2] != tokens:
        raise SystemExit(f'{path.name}: engine {entries[-1][2]}, parse {tokens}, spelled {spelled}')
    stored = sum(1 + len(row[4]) for row in entries)
    if stored != entries[-1][1]:
        raise SystemExit('stored bytes differ')
    return [{'corpus': corpus, 'L': limit, 'arm': 'greedy-polish', 'K': budget, 'B': b,
             'entries': len(entries), 'stored_bytes': stored, 'files': len(docs), 'spelled': spelled,
             'emissions': tokens, 'emissions_on_spelled': tokens, 'verified': True}
            for b in GRID_B if b is None or stored <= b]


def main():
    private, run, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    CORPUS.update(load_corpus(private, HERE / 'manifest.json'))
    jobs = []
    for corpus in ('python', 'javascript', 'both'):
        for limit in GRID_L:
            for arm in ARMS:
                if (run / 'chains' / f'{corpus}-L{limit}-{arm}.txt').exists():
                    jobs.append((corpus, limit, arm, str(run / 'chains')))
    os.nice(19)
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        checked = pool.map(check_chain, jobs, chunksize=1)
    rows = [row for item in checked for row in item['rows']]
    polish_jobs = []
    for path in sorted((run / 'chains').glob('*-polish-K*.txt')):
        corpus, rest = path.stem.split('-L', 1)
        limit, tail = rest.split('-polish-K')
        polish_jobs.append((corpus, int(limit), int(tail), str(run / 'chains')))
    if polish_jobs:
        with multiprocessing.get_context('fork').Pool(workers) as pool:
            rows += [row for part in pool.map(check_polish, polish_jobs, chunksize=1) for row in part]
    summary = {'schema': 'gamma.fixed-source-verification.v1', 'chains': len(checked),
               'cells': len(rows), 'polished_dictionaries': len(polish_jobs),
               'stopped_chains': [(c['corpus'], c['L'], c['arm']) for c in checked if c['stopped']],
               'reachability': {f"{c['corpus']}-L{c['L']}-{c['arm']}": c['reachable']
                                for c in checked if c['reachable']},
               'chain_meta': {f"{c['corpus']}-L{c['L']}-{c['arm']}":
                              {'candidates': c['candidates'], 'seconds': c['seconds']} for c in checked},
               'rows': rows}
    output.write_text(json.dumps(summary, separators=(',', ':')) + '\n')
    series = {f"{c['corpus']}-L{c['L']}-{c['arm']}": c['chain'] for c in checked}
    (output.parent / 'chains.json').write_text(json.dumps(series, separators=(',', ':')))
    print(f"verified {len(checked)} chains, {len(rows)} cells, "
          f"{len(polish_jobs)} polished dictionaries, stopped {len(summary['stopped_chains'])}")


if __name__ == '__main__':
    main()
