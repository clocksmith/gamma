#!/usr/bin/env python3
"""Rechecks a v2 dual certificate in exact integers, without bound.c.

For integer prices u >= 0 on occurrences of strings the policy allows (scaled by
65536), every dictionary D of at most K entries that spells all files satisfies

    65536 * emissions >= sum over files of shortest path with edge cost 65536 + u
                         - sum of the K largest per-string price totals.

    check_bound.py <private folder> <corpus> <policy> <certificate> [...]
"""
import hashlib
import json
import struct
import sys
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / 'fixed-source-v1' / 'manifest.json'
SCALE = 65536
MAGIC = 0x32534642
POLICY_CODE = {'s1-whole': 1, 's1-nowhole': 2, 's2-nowhole': 3}


def corpus(private, name):
    rows = json.loads(MANIFEST.read_text())['problems']
    parts = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (Path(private) / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit('hash mismatch')
            docs.append(raw)
        parts[language] = docs
    return parts['python'] + parts['javascript'] if name == 'both' else parts[name]


def eligible_at(docs, limit, policy):
    """For each file and start, the lengths of strings the policy allows there."""
    whole = set(docs)
    sizes = {len(raw) for raw in docs}
    if policy in ('s1-whole', 's1-nowhole'):
        keep_whole = policy == 's1-whole'
        lengths = []
        for raw in docs:
            rows = []
            for at in range(len(raw)):
                row = [1]
                for length in range(2, min(limit, len(raw) - at) + 1):
                    if keep_whole or length not in sizes or raw[at:at + length] not in whole:
                        row.append(length)
                rows.append(row)
            lengths.append(rows)
        return lengths
    if policy != 's2-nowhole':
        raise SystemExit('unknown policy')
    lengths = [[[1] for _ in raw] for raw in docs]
    alive = [bytearray(b'\1' * len(raw)) for raw in docs]
    for length in range(2, limit + 1):
        owner, shared = {}, set()
        for index, raw in enumerate(docs):
            flags = alive[index]
            for at in range(len(raw) - length + 1):
                if not flags[at]:
                    continue
                piece = raw[at:at + length]
                mark = owner.get(piece)
                if mark is None:
                    owner[piece] = index
                elif mark != index:
                    shared.add(piece)
        for index, raw in enumerate(docs):
            flags = alive[index]
            for at in range(len(raw)):
                if not flags[at]:
                    continue
                if at + length <= len(raw) and raw[at:at + length] in shared:
                    if raw[at:at + length] not in whole:
                        lengths[index][at].append(length)
                else:
                    flags[at] = 0
    return lengths


def check(docs, lengths, path, limit_expected, policy):
    data = Path(path).read_bytes()
    magic, code, limit, budget, count = struct.unpack_from('<5I', data)
    if magic != MAGIC or code != POLICY_CODE[policy] or limit != limit_expected or len(data) != 20 + 12 * count:
        raise SystemExit(f'{path}: malformed certificate or wrong policy')
    values = array('I')
    values.frombytes(data[20:])
    if sys.byteorder != 'little':
        values.byteswap()
    starts, offset, doc_of = {}, 0, []
    for index, raw in enumerate(docs):
        starts[index] = offset
        doc_of.extend([index] * len(raw))
        offset += len(raw)
    price, totals = {}, {}
    for row in range(count):
        position, length, value = values[3 * row], values[3 * row + 1], values[3 * row + 2]
        if position >= len(doc_of):
            raise SystemExit(f'{path}: a price outside the corpus')
        index = doc_of[position]
        at = position - starts[index]
        if length not in lengths[index][at] or value == 0 or (index, at, length) in price:
            raise SystemExit(f'{path}: a price on a string that is not eligible')
        price[(index, at, length)] = value
        piece = docs[index][at:at + length]
        totals[piece] = totals.get(piece, 0) + value
    path_total = 0
    for index, raw in enumerate(docs):
        size = len(raw)
        best = [None] * (size + 1)
        best[0] = 0
        for at in range(size):
            here = best[at]
            for length in lengths[index][at]:
                cost = here + SCALE + price.get((index, at, length), 0)
                if best[at + length] is None or cost < best[at + length]:
                    best[at + length] = cost
        path_total += best[size]
    top = sum(sorted(totals.values(), reverse=True)[:budget])
    value = path_total - top
    return {'policy': policy, 'K': budget, 'L': limit, 'nonzero_prices': count, 'exact_value': value,
            'lower_bound': -((-value) // SCALE)}


def main():
    private, name, policy = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    paths = sys.argv[4:]
    docs = corpus(private, name)
    limit = struct.unpack_from('<5I', Path(paths[0]).read_bytes())[2]
    lengths = eligible_at(docs, limit, policy)
    for path in paths:
        row = check(docs, lengths, path, limit, policy)
        row['corpus'] = name
        row['certificate_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
