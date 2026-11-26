#!/usr/bin/env python3
"""Independent byte accountant for short-record random-access codecs.

Standard library only. It imports nothing from any codec, baseline harness or scorer, and it never
uses a producer's own size numbers to compute a size. It reads the artifact files a codec emitted
and measures what a decoder must hold to return any one record:

  header      container header bytes
  dictionary  dictionary entries, including their own length bytes
  model       code tables, symbol tables, model weights
  index       the random-access offsets
  framing     bytes of a stored record unit that are container format (length prefixes)
  payload     everything else in the stored record units

An artifact set is one directory: the artifact files plus `artifacts.json`, which says which role
each file plays. Every other file in the directory must be listed, so no file can be left out of the
total. The manifest is description, not data: a decoder must not need it, and it is not counted.

    {"records": 3,
     "files": [
       {"path": "header.bin",     "role": "header"},
       {"path": "dictionary.bin", "role": "dictionary"},
       {"path": "index.bin",      "role": "index", "offset_width": 2, "offsets": "starts+end", "into": "units.bin"},
       {"path": "units.bin",      "role": "units", "unit_framing": "u8-length-prefix"}
     ]}

Roles: the six above, `units` (stored record units, split into framing and payload by walking them
with a framing rule implemented here), and `archive` (one opaque blob: counted in full, but its
components cannot be checked one by one).

    python3 -B byte_accountant.py ARTIFACT_DIR [--report REPORT.json] [--test DIR] [--train DIR]

prints the measured breakdown and, with --report, every disagreement; exit status 1 on any problem.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

COMPONENTS = ('header', 'dictionary', 'model', 'index', 'framing', 'payload')
ROLES = COMPONENTS + ('units', 'archive')
MANIFEST = 'artifacts.json'
UNIT_FRAMINGS = ('u8-length-prefix', 'u16le-length-prefix', 'uvarint-length-prefix')
OFFSET_LAYOUTS = ('starts', 'starts+end')
LEAK_MIN_LEN = 8


class AccountingError(Exception):
    """The artifact set cannot be accounted, or a report disagrees with the accounting."""


def _walk_units(data: bytes, framing: str) -> tuple[list[int], int]:
    """Unit start offsets and total framing bytes. The walk must end exactly at the end of the file."""
    starts, framing_bytes, pos = [], 0, 0
    while pos < len(data):
        starts.append(pos)
        if framing == 'u8-length-prefix':
            n, head = data[pos], 1
        elif framing == 'u16le-length-prefix':
            if pos + 2 > len(data):
                raise AccountingError(f'truncated 2-byte length prefix at offset {pos}')
            n, head = int.from_bytes(data[pos:pos + 2], 'little'), 2
        elif framing == 'uvarint-length-prefix':
            n, shift, head = 0, 0, 0
            while True:
                if pos + head >= len(data) or head > 9:
                    raise AccountingError(f'bad varint length prefix at offset {pos}')
                b = data[pos + head]
                n |= (b & 0x7F) << shift
                shift += 7
                head += 1
                if not b & 0x80:
                    break
        else:
            raise AccountingError(f'unknown unit_framing {framing!r}; known: {", ".join(UNIT_FRAMINGS)}')
        pos += head + n
        framing_bytes += head
        if pos > len(data):
            raise AccountingError(f'unit at offset {starts[-1]} runs past the end of the file')
    return starts, framing_bytes


def _read_offsets(data: bytes, width: int) -> list[int]:
    if width < 1 or len(data) % width:
        raise AccountingError(f'index of {len(data)} bytes is not a whole number of {width}-byte offsets')
    return [int.from_bytes(data[i:i + width], 'little') for i in range(0, len(data), width)]


def load_artifact_set(artifact_dir: str | os.PathLike) -> tuple[dict, dict[str, bytes]]:
    root = Path(artifact_dir)
    mpath = root / MANIFEST
    if not mpath.is_file():
        raise AccountingError(f'no {MANIFEST} in the artifact set')
    manifest = json.loads(mpath.read_text(encoding='utf-8'))
    entries = manifest.get('files')
    if not isinstance(entries, list) or not entries:
        raise AccountingError('manifest lists no files')
    blobs: dict[str, bytes] = {}
    for e in entries:
        rel = e.get('path')
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise AccountingError(f'bad artifact path {rel!r}')
        if rel in blobs:
            raise AccountingError(f'{rel} is listed twice')
        if e.get('role') not in ROLES:
            raise AccountingError(f'{rel}: role {e.get("role")!r} is not one of {", ".join(ROLES)}')
        p = root / rel
        if p.is_symlink() or not p.is_file():
            raise AccountingError(f'{rel} is listed but is not a regular file in the artifact set')
        blobs[rel] = p.read_bytes()
    on_disk = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    unlisted = sorted(on_disk - set(blobs) - {MANIFEST})
    if unlisted:
        raise AccountingError(f'files in the artifact set that the manifest does not list: {", ".join(unlisted)}')
    return manifest, blobs


def account(artifact_dir: str | os.PathLike) -> dict:
    """Measure the decoder-visible breakdown from the artifact files."""
    manifest, blobs = load_artifact_set(artifact_dir)
    acct = dict.fromkeys(COMPONENTS, 0)
    opaque = 0
    unit_starts: dict[str, list[int]] = {}
    for e in manifest['files']:
        data, role = blobs[e['path']], e['role']
        if role == 'units':
            starts, framing = _walk_units(data, e.get('unit_framing'))
            unit_starts[e['path']] = starts
            acct['framing'] += framing
            acct['payload'] += len(data) - framing
        elif role == 'archive':
            opaque += len(data)
        else:
            acct[role] += len(data)
    n_records = manifest.get('records')
    if unit_starts and n_records is not None:
        for rel, starts in unit_starts.items():
            if len(starts) != n_records:
                raise AccountingError(f'{rel} holds {len(starts)} units, manifest says {n_records} records')
    for e in manifest['files']:
        if e['role'] != 'index' or 'offset_width' not in e:
            continue
        offs = _read_offsets(blobs[e['path']], int(e['offset_width']))
        into = e.get('into')
        if into is not None:
            if into not in blobs:
                raise AccountingError(f'{e["path"]} points into {into!r}, which is not in the artifact set')
            end = len(blobs[into])
            layout = e.get('offsets', 'starts')
            if layout not in OFFSET_LAYOUTS:
                raise AccountingError(f'{e["path"]}: offsets {layout!r} is not one of {", ".join(OFFSET_LAYOUTS)}')
            starts = offs[:-1] if layout == 'starts+end' else offs
            if layout == 'starts+end' and offs[-1] != end:
                raise AccountingError(f'{e["path"]}: last offset {offs[-1]} is not the end of {into} ({end})')
            if any(b < a for a, b in zip(offs, offs[1:])) or any(o > end for o in offs):
                raise AccountingError(f'{e["path"]}: offsets are not nondecreasing within {into}')
            if into in unit_starts and starts != unit_starts[into]:
                raise AccountingError(f'{e["path"]}: offsets {starts} are not the unit boundaries {unit_starts[into]} of {into}')
            if n_records is not None and len(starts) != n_records:
                raise AccountingError(f'{e["path"]}: {len(starts)} offsets for {n_records} records')
    total = sum(len(b) for b in blobs.values())
    if sum(acct.values()) + opaque != total:   # cannot happen; kept as the invariant this module promises
        raise AccountingError('components do not sum to the artifact bytes')
    return {**acct, 'opaque': opaque, 'total': total, 'records': n_records,
            'files': {rel: len(b) for rel, b in sorted(blobs.items())}}


def check_report(report: dict, measured: dict, *, model_includes_dictionary: bool = False) -> list[str]:
    """Problems with a producer's size report, judged against `account()` output.

    `report` is {"total": n, "header": n, "dictionary": n, ...} or the same under a "bytes" key.
    A component the artifacts contain must be reported, and equal what was measured. With
    `model_includes_dictionary`, a report that folds the dictionary into `model` (as a harness with
    one model field does) is compared with measured dictionary + model.
    """
    rep = report.get('bytes', report)
    problems = []
    if not isinstance(rep.get('total'), int):
        return ['report has no integer total']
    want = {c: measured[c] for c in COMPONENTS}
    if model_includes_dictionary:
        want['model'] += want.pop('dictionary')
    if measured['opaque']:
        # One opaque archive: components cannot be checked one by one, only that they are all there.
        missing = [c for c in want if c not in rep]
        if missing:
            problems.append(f'report omits {", ".join(missing)} (an opaque archive must still be split in full)')
    else:
        for c, n in want.items():
            if c not in rep:
                if n:
                    problems.append(f'report omits {c} bytes ({n} in the artifacts)')
            elif rep[c] != n:
                problems.append(f'{c}: reported {rep[c]}, artifacts hold {n}')
    parts = sum(v for c, v in rep.items() if c in want and isinstance(v, int))
    if parts != rep['total']:
        problems.append(f'reported components sum to {parts}, reported total is {rep["total"]}')
    if rep['total'] != measured['total']:
        problems.append(f'reported total {rep["total"]} != {measured["total"]} bytes in the artifact files')
    if 'records' in report and measured['records'] is not None and report['records'] != measured['records']:
        problems.append(f'reported {report["records"]} records, artifacts hold {measured["records"]}')
    return problems


def check_leakage(stored: bytes, test_records, train_records=(), *, min_len: int = LEAK_MIN_LEN) -> list[str]:
    """Test bytes found in stored dictionary or model bytes.

    A run of at least `min_len` bytes of a test record that appears in `stored` and in no training
    record is a leak. So is a byte value that occurs in `stored` and in a test record but in no
    training record, unless `stored` carries the whole 256-value alphabet: a dictionary trained on
    training records alone has no way to contain it.
    """
    problems = []
    train = list(train_records)
    stored_grams = {stored[i:i + min_len] for i in range(len(stored) - min_len + 1)}
    train_grams = {r[i:i + min_len] for r in train for i in range(len(r) - min_len + 1)}
    for k, rec in enumerate(test_records):
        hits = [i for i in range(len(rec) - min_len + 1)
                if rec[i:i + min_len] in stored_grams and rec[i:i + min_len] not in train_grams]
        if hits:
            i = hits[0]
            j = i + min_len
            while j < len(rec) and rec[i:j + 1] in stored and rec[i:j + 1] not in b'\0'.join(train):
                j += 1
            problems.append(f'test record {k}: {j - i} bytes at offset {i} are in the stored bytes and in no '
                            f'training record: {rec[i:j]!r}')
    stored_values = set(stored)
    if len(stored_values) < 256:
        test_only = (set().union(*map(set, test_records)) if test_records else set()) - set().union(*map(set, train))
        leaked = sorted(stored_values & test_only)
        if leaked:
            problems.append(f'stored bytes contain byte values seen only in test records: {bytes(leaked)!r}')
    return problems


def stored_model_bytes(artifact_dir: str | os.PathLike) -> bytes:
    """Concatenated dictionary and model files: where trained content lives."""
    manifest, blobs = load_artifact_set(artifact_dir)
    return b''.join(blobs[e['path']] for e in manifest['files'] if e['role'] in ('dictionary', 'model'))


def require(artifact_dir, report: dict, *, test_records=None, train_records=(), leak_min_len: int = LEAK_MIN_LEN,
            model_includes_dictionary: bool = False) -> dict:
    """Account, check the report and, given test records, the leakage guard. Raise on any problem."""
    measured = account(artifact_dir)
    problems = check_report(report, measured, model_includes_dictionary=model_includes_dictionary)
    if test_records is not None:
        problems += check_leakage(stored_model_bytes(artifact_dir), test_records, train_records, min_len=leak_min_len)
    if problems:
        raise AccountingError('; '.join(problems))
    return measured


def _records_from_dir(path: str) -> list[bytes]:
    root = Path(path)
    return [p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('artifact_dir')
    ap.add_argument('--report', help='producer size report (JSON) to check against the artifacts')
    ap.add_argument('--test', help='directory of test records, one per file, for the leakage guard')
    ap.add_argument('--train', help='directory of training records, one per file')
    ap.add_argument('--leak-min-len', type=int, default=LEAK_MIN_LEN)
    ap.add_argument('--model-includes-dictionary', action='store_true')
    a = ap.parse_args(argv)
    try:
        measured = account(a.artifact_dir)
    except AccountingError as exc:
        print(f'FAIL: {exc}')
        return 1
    print(json.dumps(measured, indent=2))
    problems = []
    if a.report:
        report = json.loads(Path(a.report).read_text(encoding='utf-8'))
        problems += check_report(report, measured, model_includes_dictionary=a.model_includes_dictionary)
    if a.test:
        problems += check_leakage(stored_model_bytes(a.artifact_dir), _records_from_dir(a.test),
                                  _records_from_dir(a.train) if a.train else (), min_len=a.leak_min_len)
    for p in problems:
        print(f'FAIL: {p}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
