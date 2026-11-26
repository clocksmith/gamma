#!/usr/bin/env python3
"""Train the five arms, the character reference and the zstd dictionary on
CodeNet `primary` only, and write the frozen headers (dictionary + code table).

Reads no file outside the frozen `primary` training split, except that it
writes path lists for `primary` (train) and `secondary` (development) without
opening the development files' contents for any decision.

    python3 train_arms.py --work WORKDIR [--compare-chains DIR] [--jobs N]

Outputs `frozen/` next to this file. See PREREGISTRATION.md.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bits_oh as B  # noqa: E402

LITERALS = HERE.parent
CODENET = LITERALS / 'codenet-replication-v1'
ENGINE_SRC = LITERALS / 'fixed-source-v3' / 'engine.c'
FROZEN = HERE / 'frozen'

CAPS = (256, 4096)
MAX_LEN = 16
ENGINE_KMAX = 4096
ENGINE_LIMIT_SECONDS = 300
POLICY = 's1-whole'
PREFIX_STEP = {256: 16, 4096: 64}
SHORTLIST = 3
ZSTD_MAXDICT = 8192
ENGINE_MODES = {'bpe': 'bpe', 'length': 'freq-occ', 'token': 'greedy-entry', 'gain-per-byte': 'greedy-byte'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_split(split):
    """Files in the frozen order: every Python file in pair order, then every
    JavaScript file. unit = CodeNet problem id."""
    manifest = json.loads((CODENET / 'manifest.json').read_text())
    files = []
    for lang in ('python', 'javascript'):
        for pair in manifest['splits'][split]['pairs']:
            rec = pair[lang]
            files.append({
                'path': 'codenet-replication-v1/' + rec['path'],
                'unit': pair['p_id'],
                'lang': lang,
                'bytes': rec['bytes'],
                'sha256': rec['sha256'],
            })
    return files


def read_files(files):
    docs = []
    for f in files:
        raw = (LITERALS / f['path']).read_bytes()
        if sha256(raw) != f['sha256']:
            raise SystemExit(f'hash mismatch: {f["path"]}')
        docs.append(raw)
    return docs


def run_engine(work, mode, list_file, receipt):
    binary = work / 'engine'
    if not binary.exists():
        subprocess.run(['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(binary), str(ENGINE_SRC), '-lm'],
                       check=True)
    out = work / 'chains' / f'{mode}.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['FSV3_RECEIPT'] = receipt
    env.pop('FSV3_CUTS', None)
    env.pop('FSV3_GROUPS', None)
    t0 = time.perf_counter()
    subprocess.run([str(binary), mode, POLICY, str(MAX_LEN), str(ENGINE_KMAX), str(ENGINE_LIMIT_SECONDS),
                    str(list_file), str(out)], env=env, check=True)
    return out, time.perf_counter() - t0


def chain_entries(path):
    """Entries of an engine chain in the order they were added."""
    entries = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if parts and parts[0] == 'E':
            entries.append(bytes.fromhex(parts[5]))
    return entries


def raw_frequency_order(docs):
    """Every string of 2..16 bytes inside one training file, ranked by
    overlapping occurrence count, then files, then shorter, then bytewise."""
    occ = Counter()
    nfiles = Counter()
    for raw in docs:
        seen = set()
        n = len(raw)
        for l in range(2, MAX_LEN + 1):
            for i in range(n - l + 1):
                seen.add(raw[i:i + l])
        for l in range(2, MAX_LEN + 1):
            occ.update(raw[i:i + l] for i in range(n - l + 1))
        nfiles.update(seen)
    return sorted(occ, key=lambda s: (-occ[s], -nfiles[s], len(s), s))


_DOCS = None


def _init(docs):
    global _DOCS
    _DOCS = docs


def _one_shot(entries):
    """Complete training archive bytes with the table fitted to the
    minimum-token parse (no reparse). Used only to shortlist prefixes."""
    d = B.Dictionary(entries)
    counts = [0] * (d.n + 2)
    for raw in _DOCS:
        for sym in B.parse_tokens(d.edges(raw)):
            counts[sym] += 1
    counts[d.EOF] = len(_DOCS)
    lengths = B.huffman_lengths([c if c > 0 else 1 for c in counts])
    bits = sum(c * l for c, l in zip(counts, lengths))
    header = len(B.build_header(entries, lengths))
    return header + len(B.varint(len(_DOCS))) + (bits + 7) // 8


def _fit(entries):
    d = B.Dictionary(entries)
    edges = [d.edges(raw) for raw in _DOCS]
    lengths, counts, bits, passes = B.fit_table(d, edges)
    header = B.build_header(entries, lengths)
    complete = len(header) + len(B.varint(len(_DOCS))) + (bits + 7) // 8
    return {'lengths': lengths, 'counts': counts, 'payload_bits': bits, 'passes': passes,
            'header_bytes': len(header), 'complete_bytes': complete}


def _describe(args):
    """Train-side facts for one frozen dictionary, and its cross-problem variant."""
    name, entries, units = args
    d = B.Dictionary(entries)
    edges = [d.edges(raw) for raw in _DOCS]
    fit = _fit(entries)
    lengths = fit['lengths']
    tokens = sum(len(B.parse_tokens(e)) for e in edges)
    uses = [0] * d.n
    unit_sets = [set() for _ in range(d.n)]
    for e, unit in zip(edges, units):
        syms, _ = B.parse_bits(e, lengths, d.ESC)
        for s in syms:
            uses[s] += 1
            unit_sets[s].add(unit)
    train_units = [len(u) for u in unit_sets]
    keep = [e for i, e in enumerate(entries) if len(e) == 1 or train_units[i] >= 2]
    return name, fit, tokens, uses, train_units, keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True, help='scratch directory (not committed)')
    ap.add_argument('--compare-chains', help='directory of earlier engine chains to compare byte for byte')
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    FROZEN.mkdir(exist_ok=True)
    (FROZEN / 'sets').mkdir(exist_ok=True)
    t_start = time.perf_counter()

    train = load_split('primary')
    dev = load_split('secondary')
    for name, files in (('train', train), ('dev', dev)):
        (FROZEN / 'sets' / f'{name}.json').write_text(json.dumps({
            'set': name,
            'source': 'IBM Project CodeNet v1.0.0 (CDLA-Permissive-2.0), codenet-replication-v1 '
                      + ('primary' if name == 'train' else 'secondary'),
            'unit': 'CodeNet problem id',
            'files': files,
        }, indent=1) + '\n')
    docs = read_files(train)
    units = [f['unit'] for f in train]
    singles = [bytes([b]) for b in sorted({b for raw in docs for b in raw})]
    print(f'train: {len(docs)} files, {sum(map(len, docs))} bytes, {len(singles)} distinct bytes', flush=True)

    list_file = work / 'train.list'
    list_file.write_text('\n'.join(str(LITERALS / f['path']) for f in train) + '\n')
    manifest_sha = sha256((CODENET / 'manifest.json').read_bytes())
    engine_sha = sha256(ENGINE_SRC.read_bytes())
    receipt = f'manifest={manifest_sha} split=primary pool=both cuts=none impl={engine_sha} run=objective-holdout-v1'
    orders = {}
    engine_seconds = {}
    chain_match = {}
    for arm, mode in ENGINE_MODES.items():
        path, seconds = run_engine(work, mode, list_file, receipt)
        entries = chain_entries(path)
        if entries[:len(singles)] != singles:
            raise SystemExit(f'{mode}: chain does not start with the training alphabet')
        multi = entries[len(singles):]
        if any(not 2 <= len(e) <= MAX_LEN for e in multi) or len(set(multi)) != len(multi):
            raise SystemExit(f'{mode}: illegal chain entry')
        orders[arm] = multi
        engine_seconds[arm] = round(seconds, 1)
        if args.compare_chains:
            old = Path(args.compare_chains) / f'both-L{MAX_LEN}-{mode}.txt'
            chain_match[arm] = chain_entries(old) == entries if old.exists() else None
        print(f'engine {mode}: {len(multi)} multi-byte entries in {seconds:.1f}s, '
              f'matches earlier chain: {chain_match.get(arm)}', flush=True)
    t0 = time.perf_counter()
    orders['freq'] = raw_frequency_order(docs)
    print(f'raw frequency order: {len(orders["freq"])} strings in {time.perf_counter() - t0:.1f}s', flush=True)

    joined = set()
    for raw in docs:
        for l in range(2, MAX_LEN + 1):
            for i in range(len(raw) - l + 1):
                joined.add(raw[i:i + l])
    for arm in ('bpe', 'length', 'token', 'gain-per-byte'):
        if any(e not in joined for e in orders[arm]):
            raise SystemExit(f'{arm}: entry does not occur inside one training file')
    del joined

    dictionaries = {}
    selection = {}
    with Pool(args.jobs, initializer=_init, initargs=(docs,)) as pool:
        for cap in CAPS:
            budget = cap - len(singles) - 1  # one slot is the escape
            if budget < 1:
                raise SystemExit('cap leaves no room for fragments')
            dictionaries[('chars', cap)] = list(singles)
            for arm in ('bpe', 'freq', 'length', 'token'):
                dictionaries[(arm, cap)] = singles + orders[arm][:budget]
            # Complete-archive-byte selection: the prefix of the token-gain or
            # gain-per-stored-byte order whose complete training archive is smallest.
            step = PREFIX_STEP[cap]
            sizes = sorted(set(range(0, budget + 1, step)) | {budget})
            cands = []
            for order in ('token', 'gain-per-byte'):
                seen = set()
                for m in sizes:
                    m = min(m, len(orders[order]))
                    if m not in seen:
                        seen.add(m)
                        cands.append((order, m))
            shot = pool.map(_one_shot, [singles + orders[o][:m] for o, m in cands], chunksize=1)
            short = []
            for order in ('token', 'gain-per-byte'):
                rows = sorted((b, m) for (o, m), b in zip(cands, shot) if o == order)
                short += [(order, m) for _, m in rows[:SHORTLIST]]
            fits = pool.map(_fit, [singles + orders[o][:m] for o, m in short], chunksize=1)
            ranked = sorted((f['complete_bytes'], m, 0 if o == 'token' else 1, o) for (o, m), f in zip(short, fits))
            _, m_best, _, o_best = ranked[0]
            dictionaries[('bytes', cap)] = singles + orders[o_best][:m_best]
            selection[str(cap)] = {
                'budget_multi_byte_entries': budget,
                'prefix_step': step,
                'one_shot_complete_bytes': [{'order': o, 'prefix': m, 'bytes': b} for (o, m), b in zip(cands, shot)],
                'shortlist_fixed_point': [{'order': o, 'prefix': m, 'bytes': f['complete_bytes']}
                                          for (o, m), f in zip(short, fits)],
                'chosen': {'order': o_best, 'prefix': m_best},
            }
            print(f'cap {cap}: budget {budget}, byte selection chose {o_best} prefix {m_best}', flush=True)

        jobs = [(f'{arm}-K{cap}', entries, units) for (arm, cap), entries in sorted(dictionaries.items())]
        described = pool.map(_describe, jobs, chunksize=1)
        base = {}
        variants = []
        for name, fit, tokens, uses, train_units, keep in described:
            base[name] = (fit, tokens, uses, train_units)
            if not name.startswith('chars') and len(keep) < len(dict(jobs_index(jobs))[name]):
                variants.append((name + '.xp', keep, units))
        described_xp = pool.map(_describe, variants, chunksize=1)

    summary = {
        'schema': 'gamma.bits-objective-holdout.train-summary.v1',
        'train_files': len(docs),
        'train_bytes': sum(map(len, docs)),
        'train_problems': len(set(units)),
        'singleton_bytes': len(singles),
        'max_entry_len': MAX_LEN,
        'engine': {'source_sha256': engine_sha, 'policy': POLICY, 'kmax': ENGINE_KMAX,
                   'limit_seconds': ENGINE_LIMIT_SECONDS, 'seconds': engine_seconds,
                   'matches_earlier_chain': chain_match},
        'manifest_sha256': manifest_sha,
        'byte_selection': selection,
        'headers': {},
    }
    entry_lists = dict(jobs_index(jobs))
    entry_lists.update({name: keep for name, keep, _ in variants})
    for name, fit, tokens, uses, train_units, _ in list(described) + list(described_xp):
        entries = entry_lists[name]
        header = B.build_header(entries, fit['lengths'])
        (FROZEN / f'{name}.boh').write_bytes(header)
        arm, cap = name.split('.')[0].rsplit('-K', 1)
        summary['headers'][name] = {
            'arm': arm,
            'cap': int(cap),
            'variant': 'cross-problem entries only' if name.endswith('.xp') else 'base',
            'entries': len(entries),
            'slots_used_with_escape': len(entries) + 1,
            'multi_byte_entries': sum(1 for e in entries if len(e) > 1),
            'dictionary_bytes': sum(1 + len(e) for e in entries),
            'header_bytes': len(header),
            'header_sha256': sha256(header),
            'table_passes': fit['passes'],
            'max_code_length': max(fit['lengths']),
            'train_min_tokens': tokens,
            'train_payload_bits': fit['payload_bits'],
            'train_complete_bytes': fit['complete_bytes'],
            'train_uses': uses,
            'train_units': train_units,
        }
        print(f'{name}: entries {len(entries)}, header {len(header)} B, train tokens {tokens}, '
              f'train complete {fit["complete_bytes"]} B', flush=True)

    # zstd dictionary, trained on the same files with the earlier run's settings.
    zstd = shutil.which('zstd')
    if not zstd:
        raise SystemExit('zstd not found')
    with tempfile.TemporaryDirectory() as td:
        paths = []
        n_py = sum(1 for f in train if f['lang'] == 'python')
        for i, raw in enumerate(docs):
            p = Path(td) / (f'tp{i:04d}.py' if i < n_py else f'tj{i - n_py:04d}.js')
            p.write_bytes(raw)
            paths.append(str(p))
        out = FROZEN / 'zstd-train-8k.dict'
        subprocess.run([zstd, '--train', f'--maxdict={ZSTD_MAXDICT}', '-q', '-f', '-o', str(out)] + paths, check=True)
    version = subprocess.run([zstd, '--version'], capture_output=True, text=True).stdout.strip()
    summary['zstd'] = {'version': version, 'maxdict': ZSTD_MAXDICT, 'dict_bytes': out.stat().st_size,
                       'dict_sha256': sha256(out.read_bytes())}
    summary['seconds'] = round(time.perf_counter() - t_start, 1)
    (FROZEN / 'train-summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(f'done in {summary["seconds"]}s', flush=True)


def jobs_index(jobs):
    return [(name, entries) for name, entries, _ in jobs]


if __name__ == '__main__':
    sys.exit(main())
