#!/usr/bin/env python3
"""Score every frozen header on one set of files. Changes nothing in `frozen/`.

    python3 score.py --set sets/NAME.json --root LITERALS_DIR --out OUTDIR [--jobs N]

For each frozen header (dictionary + code table) it reports the exact minimum
token count, writes the real archive encoded with the frozen table and a
minimum-bit parse, and measures what each multi-byte entry is worth on this
set by removing it and reparsing. It also runs the zstd baseline with the
frozen trained dictionary. Python 3 standard library plus the `zstd` binary.
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from math import comb
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bits_oh as B  # noqa: E402

FROZEN = HERE / 'frozen'
PAIRS = [('token', 'bpe'), ('bytes', 'bpe'), ('bytes', 'token'), ('token', 'freq'), ('token', 'length'),
         ('bpe', 'chars'), ('token', 'chars'), ('bytes', 'chars')]
TRAIN_CLASSES = ('0', '1', '2-3', '4+')


def train_class(units):
    if units <= 1:
        return str(units)
    return '2-3' if units <= 3 else '4+'


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


_DOCS = None
_UNITS = None
_OUT = None
_SET = None
_TRAIN = None


def _init(docs, units, out, set_name, train_headers):
    global _DOCS, _UNITS, _OUT, _SET, _TRAIN
    _DOCS, _UNITS, _OUT, _SET, _TRAIN = docs, units, out, set_name, train_headers


def score_header(name):
    header = (FROZEN / f'{name}.boh').read_bytes()
    entries, lengths, used = B.parse_header(header)
    if used != len(header):
        raise SystemExit(f'{name}: trailing bytes in header')
    d = B.Dictionary(entries)
    esc = d.ESC
    docs = _DOCS
    edges = [d.edges(raw) for raw in docs]
    tok = [B.parse_tokens(e) for e in edges]
    bit = []
    bit_cost = []
    for e in edges:
        syms, c = B.parse_bits(e, lengths, esc)
        bit.append(syms)
        bit_cost.append(c)
    payload, per_file_bits = B.encode_payload(d, lengths, docs, bit)
    for c, b in zip(bit_cost, per_file_bits):
        if c + lengths[d.EOF] != b:
            raise AssertionError('encoded bits differ from the parse cost')
    archive = header + B.varint(len(docs)) + payload
    if B.decode_archive(archive) != docs:
        raise AssertionError(f'{name}: self-check decode failed')
    arch_dir = _OUT / 'archives' / _SET
    arch_dir.mkdir(parents=True, exist_ok=True)
    (arch_dir / f'{name}.boh').write_bytes(archive)

    n = d.n
    lens = [len(e) for e in entries]
    multi = [i for i in range(n) if lens[i] > 1]
    meta = _TRAIN[name]
    train_units = meta['train_units']

    hist = [0] * (B.MAX_ENTRY_LEN + 1)
    tok_used = set()
    escapes_tok = 0
    for syms in tok:
        for s in syms:
            if s == esc:
                escapes_tok += 1
                hist[1] += 1
            else:
                hist[lens[s]] += 1
                tok_used.add(s)
    realized_multi = sum(hist[2:])

    uses = [0] * (n + 2)
    files_using = [[] for _ in range(n + 2)]
    unit_sets = [set() for _ in range(n + 2)]
    for fi, syms in enumerate(bit):
        seen = set()
        for s in syms:
            uses[s] += 1
            if s not in seen:
                seen.add(s)
                files_using[s].append(fi)
                unit_sets[s].add(_UNITS[fi])
    escapes_bit = uses[esc]

    # What each multi-byte entry is worth here: remove it, reparse the files
    # that used it with the code lengths unchanged, and recount complete bytes.
    rent = {}
    for s in multi:
        delta = 0
        for fi in files_using[s]:
            _, c = B.parse_bits(edges[fi], lengths, esc, banned=s)
            delta += c - bit_cost[fi]
        rent[s] = delta - 8 * (lens[s] + 2)  # entry length byte, entry bytes, one table byte

    by_class = {c: {'entries': 0, 'used': 0, 'uses': 0, 'bytes_covered': 0, 'pays_rent': 0, 'rent_bits': 0,
                    'within_file_repeats': 0, 'files': 0, 'units': 0} for c in TRAIN_CLASSES}
    for s in multi:
        row = by_class[train_class(train_units[s])]
        row['entries'] += 1
        row['used'] += 1 if uses[s] else 0
        row['uses'] += uses[s]
        row['bytes_covered'] += uses[s] * lens[s]
        row['pays_rent'] += 1 if rent[s] > 0 else 0
        row['rent_bits'] += rent[s]
        row['within_file_repeats'] += uses[s] - len(files_using[s])
        row['files'] += len(files_using[s])
        row['units'] += len(unit_sets[s])

    sum_uses = sum(uses[s] for s in multi)
    sum_files = sum(len(files_using[s]) for s in multi)
    sum_units = sum(len(unit_sets[s]) for s in multi)
    per_file_payload_bytes = [(b + 7) // 8 for b in per_file_bits]
    random_access = (len(header) + len(B.varint(len(docs))) + sum(per_file_payload_bytes)
                     + sum(len(B.varint(x)) for x in per_file_payload_bytes))
    result = {
        'header': name,
        'arm': meta['arm'],
        'cap': meta['cap'],
        'variant': meta['variant'],
        'entries': n,
        'slots_used_with_escape': n + 1,
        'multi_byte_entries': len(multi),
        'min_tokens': sum(len(s) for s in tok),
        'escapes_in_min_token_parse': escapes_tok,
        'distinct_entries_used_min_token_parse': len(tok_used),
        'realized_entry_length_histogram': hist,
        'mean_realized_entry_length': round(sum(map(len, docs)) / max(1, sum(len(s) for s in tok)), 4),
        'bit_parse_tokens': sum(len(s) for s in bit),
        'escapes_in_bit_parse': escapes_bit,
        'distinct_entries_used_bit_parse': sum(1 for s in range(n) if uses[s]),
        'candidate_multi_byte_matches_overlapping': sum(len(e) - 1 for ed in edges for e in ed),
        'realized_multi_byte_uses_min_token_parse': realized_multi,
        'realized_multi_byte_uses_bit_parse': sum_uses,
        'reuse': {
            'multi_byte_entries_used': sum(1 for s in multi if uses[s]),
            'multi_byte_entries_used_in_2plus_units': sum(1 for s in multi if len(unit_sets[s]) >= 2),
            'uses': sum_uses,
            'within_file_repeats': sum_uses - sum_files,
            'second_file_same_unit': sum_files - sum_units,
            'first_use_in_a_unit': sum_units,
        },
        'rent': {
            'multi_byte_entries': len(multi),
            'pay_rent': sum(1 for s in multi if rent[s] > 0),
            'do_not_pay_rent': sum(1 for s in multi if rent[s] <= 0),
            'unused': sum(1 for s in multi if not uses[s]),
            'sum_rent_bits_paying': sum(rent[s] for s in multi if rent[s] > 0),
            'sum_rent_bits_not_paying': sum(rent[s] for s in multi if rent[s] <= 0),
        },
        'by_train_reuse_class': by_class,
        'bytes': {
            'magic_and_counts': len(B.MAGIC) + len(B.varint(n)) + len(B.varint(len(docs))),
            'dictionary': sum(1 + l for l in lens),
            'table': n + 2,
            'payload': len(payload),
            'payload_bits': sum(per_file_bits),
            'header': len(header),
            'complete': len(archive),
            'dictionary_already_held': len(archive) - len(header),
            'random_access_complete': random_access,
        },
        'archive_sha256': hashlib.sha256(archive).hexdigest(),
    }
    per_entry = {
        'entry_hex': [entries[s].hex() for s in multi],
        'train_units': [train_units[s] for s in multi],
        'uses': [uses[s] for s in multi],
        'files': [len(files_using[s]) for s in multi],
        'units': [len(unit_sets[s]) for s in multi],
        'rent_bits': [rent[s] for s in multi],
    }
    per_file = {
        'tokens': [len(s) for s in tok],
        'bits': per_file_bits,
        'distinct': [len(set(s)) for s in tok],
        'escapes': [s.count(esc) for s in bit],
    }
    return name, result, per_entry, per_file


def zstd_baseline(docs, out_dir):
    zstd = shutil.which('zstd')
    version = subprocess.run([zstd, '--version'], capture_output=True, text=True).stdout.strip()
    dict_path = FROZEN / 'zstd-train-8k.dict'
    rows = {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / 'src'
        src.mkdir()
        files = []
        for i, raw in enumerate(docs):
            p = src / f'f{i:05d}'
            p.write_bytes(raw)
            files.append(p)

        def per_file(extra, label):
            z = td / f'z-{label}'
            dd = td / f'd-{label}'
            z.mkdir()
            dd.mkdir()
            subprocess.run([zstd, '-19', '-q', '-f', '--output-dir-flat', str(z)] + extra + [str(f) for f in files],
                           check=True)
            frames = [z / (f.name + '.zst') for f in files]
            subprocess.run([zstd, '-d', '-q', '-f', '--output-dir-flat', str(dd)] + extra + [str(f) for f in frames],
                           check=True)
            for f, raw in zip(files, docs):
                if (dd / f.name).read_bytes() != raw:
                    raise AssertionError('zstd round trip failed')
            return [f.stat().st_size for f in frames]

        sizes = per_file(['-D', str(dict_path)], 'dict')
        dict_bytes = dict_path.stat().st_size
        rows['zstd-19 per file, trained 8 KiB dictionary'] = {
            'dictionary': dict_bytes,
            'payload': sum(sizes),
            'complete': dict_bytes + sum(sizes),
            'dictionary_already_held': sum(sizes),
            'random_access_complete': dict_bytes + sum(sizes) + sum(len(B.varint(x)) for x in sizes),
            'per_file_bytes': sizes,
        }
        sizes = per_file([], 'plain')
        rows['zstd-19 per file, no dictionary'] = {
            'dictionary': 0, 'payload': sum(sizes), 'complete': sum(sizes), 'dictionary_already_held': sum(sizes),
            'random_access_complete': sum(sizes) + sum(len(B.varint(x)) for x in sizes), 'per_file_bytes': sizes,
        }
        solid = td / 'solid.bin'
        solid.write_bytes(b''.join(B.varint(len(raw)) + raw for raw in docs))
        for label, extra in (('zstd-19 one stream, no dictionary', []),
                             ('zstd-19 one stream, trained 8 KiB dictionary', ['-D', str(dict_path)])):
            o = td / 'solid.zst'
            back = td / 'solid.back'
            subprocess.run([zstd, '-19', '-q', '-f', '-o', str(o)] + extra + [str(solid)], check=True)
            subprocess.run([zstd, '-d', '-q', '-f', '-o', str(back)] + extra + [str(o)], check=True)
            if back.read_bytes() != solid.read_bytes():
                raise AssertionError('zstd solid round trip failed')
            dsz = dict_bytes if extra else 0
            rows[label] = {'dictionary': dsz, 'payload': o.stat().st_size, 'complete': dsz + o.stat().st_size,
                           'dictionary_already_held': o.stat().st_size, 'random_access_complete': None}
    return {'version': version, 'dict_sha256': hashlib.sha256(dict_path.read_bytes()).hexdigest(), 'rows': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', required=True)
    ap.add_argument('--root', required=True, help='directory the set manifest paths are relative to')
    ap.add_argument('--out', required=True)
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    t0 = time.perf_counter()
    spec = json.loads(Path(args.set).read_text())
    set_name = spec['set']
    root = Path(args.root)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    docs = []
    for f in spec['files']:
        raw = (root / f['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != f['sha256']:
            raise SystemExit(f'hash mismatch: {f["path"]}')
        docs.append(raw)
    units = [f['unit'] for f in spec['files']]
    summary = json.loads((FROZEN / 'train-summary.json').read_text())
    names = sorted(summary['headers'])
    for name in names:
        if hashlib.sha256((FROZEN / f'{name}.boh').read_bytes()).hexdigest() != summary['headers'][name]['header_sha256']:
            raise SystemExit(f'{name}: frozen header changed')
    with Pool(args.jobs, initializer=_init, initargs=(docs, units, out, set_name, summary['headers'])) as pool:
        scored = pool.map(score_header, names, chunksize=1)
    results = {name: r for name, r, _, _ in scored}
    per_entry = {name: e for name, _, e, _ in scored}
    per_file = {name: f for name, _, _, f in scored}

    unit_order = sorted(set(units))
    paired = []
    for cap in sorted({r['cap'] for r in results.values()}):
        for a, b in PAIRS:
            na, nb = f'{a}-K{cap}', f'{b}-K{cap}'
            if na not in per_file or nb not in per_file:
                continue
            row = {'cap': cap, 'a': a, 'b': b}
            for metric in ('tokens', 'bits'):
                ta = dict.fromkeys(unit_order, 0)
                tb = dict.fromkeys(unit_order, 0)
                for u, x, y in zip(units, per_file[na][metric], per_file[nb][metric]):
                    ta[u] += x
                    tb[u] += y
                wins = sum(1 for u in unit_order if ta[u] < tb[u])
                losses = sum(1 for u in unit_order if ta[u] > tb[u])
                sa, sb = sum(ta.values()), sum(tb.values())
                row[metric] = {'a_total': sa, 'b_total': sb, 'a_vs_b_percent': round(100.0 * (sa - sb) / sb, 3),
                               'units_a_lower': wins, 'units_a_higher': losses,
                               'units_tied': len(unit_order) - wins - losses,
                               'sign_test_two_sided_p': sign_test(wins, losses)}
            ca = results[na]['bytes']['complete']
            cb = results[nb]['bytes']['complete']
            row['complete_bytes'] = {'a': ca, 'b': cb, 'a_vs_b_percent': round(100.0 * (ca - cb) / cb, 3)}
            paired.append(row)

    langs = sorted({f['lang'] for f in spec['files']})
    by_lang = {}
    for lang in langs:
        idx = [i for i, f in enumerate(spec['files']) if f['lang'] == lang]
        by_lang[lang] = {
            'files': len(idx),
            'source_bytes': sum(len(docs[i]) for i in idx),
            'min_tokens': {name: sum(per_file[name]['tokens'][i] for i in idx) for name in names},
            'payload_bits': {name: sum(per_file[name]['bits'][i] for i in idx) for name in names},
        }

    final = {
        'schema': 'gamma.bits-objective-holdout.results.v1',
        'set': set_name,
        'set_manifest_sha256': hashlib.sha256(Path(args.set).read_bytes()).hexdigest(),
        'files': len(docs),
        'units': len(unit_order),
        'source_bytes': sum(map(len, docs)),
        'headers': results,
        'paired': paired,
        'by_language': by_lang,
        'zstd': zstd_baseline(docs, out),
        'seconds': None,
    }
    final['seconds'] = round(time.perf_counter() - t0, 1)
    (out / f'results-{set_name}.json').write_text(json.dumps(final, indent=1) + '\n')
    (out / f'entries-{set_name}.json').write_text(json.dumps(per_entry) + '\n')
    with open(out / f'per-file-{set_name}.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['file', 'unit', 'lang', 'bytes'] + [f'{n}:{m}' for n in names for m in ('tokens', 'bits', 'escapes')])
        for i, f in enumerate(spec['files']):
            row = [f['path'], f['unit'], f['lang'], len(docs[i])]
            for n in names:
                row += [per_file[n]['tokens'][i], per_file[n]['bits'][i], per_file[n]['escapes'][i]]
            w.writerow(row)
    print(f'{set_name}: {len(docs)} files, {final["source_bytes"]} bytes, {len(names)} headers, {final["seconds"]}s')
    for name in names:
        r = results[name]
        print(f'  {name:18s} entries {r["entries"]:5d}  tokens {r["min_tokens"]:7d}  complete {r["bytes"]["complete"]:7d} B'
              f'  payload {r["bytes"]["payload"]:7d} B  escapes {r["escapes_in_bit_parse"]}')
    for label, row in final['zstd']['rows'].items():
        print(f'  {label}: complete {row["complete"]} B')


if __name__ == '__main__':
    sys.exit(main())
