#!/usr/bin/env python3
"""Rechecks a dual certificate of bound.c in exact integers, without its code.

For integer prices u >= 0 on occurrences of eligible strings (scaled by 65536),
every dictionary D of at most K entries that spells all files satisfies

    65536 * emissions >= sum over files of shortest path with edge cost 65536 + u
                         - sum of the K largest per-string price totals.

    check_bound.py <private folder> <corpus> <certificate> [<certificate> ...]
"""
import hashlib
import json
import struct
import sys
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCALE = 65536


def corpus(private, name):
    rows = json.loads((HERE / 'manifest.json').read_text())['problems']
    parts = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (private / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit('hash mismatch')
            docs.append(raw)
        parts[language] = docs
    return parts['python'] + parts['javascript'] if name == 'both' else parts[name]


def eligible_at(docs, limit):
    """For each file and start, the lengths of eligible strings there."""
    whole = set(docs)
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


def check(docs, lengths, path, limit_expected):
    data = Path(path).read_bytes()
    magic, limit, budget, count = struct.unpack_from('<4I', data)
    if magic != 0x31534642 or limit != limit_expected or len(data) != 16 + 12 * count:
        raise SystemExit(f'{path}: malformed certificate')
    values = array('I')
    values.frombytes(data[16:])
    if sys.byteorder != 'little':
        values.byteswap()
    starts, offset = {}, 0
    doc_of = []
    for index, raw in enumerate(docs):
        starts[index] = offset
        doc_of.extend([index] * len(raw))
        offset += len(raw)
    price = {}
    totals = {}
    for row in range(count):
        position, length, value = values[3 * row], values[3 * row + 1], values[3 * row + 2]
        index = doc_of[position]
        at = position - starts[index]
        if length not in lengths[index][at] or value == 0:
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
    bound = -((-value) // SCALE)  # ceiling: emissions are integers
    return {'K': budget, 'L': limit, 'nonzero_prices': count, 'exact_value': value, 'lower_bound': bound}


def main():
    private, name = Path(sys.argv[1]), sys.argv[2]
    paths = sys.argv[3:]
    docs = corpus(private, name)
    limit = struct.unpack_from('<4I', Path(paths[0]).read_bytes())[1]
    lengths = eligible_at(docs, limit)
    results = []
    for path in paths:
        row = check(docs, lengths, path, limit)
        row['corpus'] = name
        row['certificate_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        results.append(row)
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
