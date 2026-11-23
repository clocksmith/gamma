#!/usr/bin/env python3
"""Checks the engine, parser and dual bound against brute force on tiny corpora.

    test_small.py <engine> <bound>
"""
import itertools
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_bound as B
import verify as V


def eligible(docs, limit):
    whole = set(docs)
    found = {bytes([b]) for raw in docs for b in raw}
    for length in range(2, limit + 1):
        for raw in docs:
            for at in range(len(raw) - length + 1):
                piece = raw[at:at + length]
                if piece not in whole and sum(piece in other for other in docs) >= 2:
                    found.add(piece)
    return sorted(found, key=lambda s: (len(s), s))


def cost(docs, entries):
    root = {}
    for entry in entries:
        V.insert(root, entry)
    total = 0
    for raw in docs:
        pieces = V.parse(raw, root)
        if pieces is None:
            return None
        if b''.join(pieces) != raw:
            raise SystemExit('parser did not reconstruct')
        total += len(pieces)
    return total


def optimum(docs, candidates, budget):
    best = None
    for size in range(1, min(budget, len(candidates)) + 1):
        for subset in itertools.combinations(candidates, size):
            value = cost(docs, subset)
            if value is not None and (best is None or value < best):
                best = value
    return best


def main():
    engine, bound = sys.argv[1], sys.argv[2]
    rng = random.Random(20261123)
    tested = gaps = 0
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        while tested < 60:
            docs = list({bytes(rng.choice(b'abc') for _ in range(rng.randint(3, 6)))
                         for _ in range(rng.randint(3, 4))})
            limit = 3
            candidates = eligible(docs, limit)
            alphabet = len({b for raw in docs for b in raw})
            if len(docs) < 3 or len(candidates) > 13 or len(candidates) <= alphabet:
                continue
            paths = []
            for index, raw in enumerate(docs):
                path = root / f'{index}.txt'
                path.write_bytes(raw)
                paths.append(str(path))
            listing = root / 'list.txt'
            listing.write_text('\n'.join(paths) + '\n')
            budget = alphabet + rng.randint(0, 2)
            best = optimum(docs, candidates, budget)
            chain = root / 'chain.txt'
            subprocess.run([engine, 'greedy-entry', str(limit), str(budget), '30', str(listing), str(chain)], check=True)
            entries = V.read_chain(chain)[0]
            built = cost(docs, [row[4] for row in entries])
            if built is None or built < best or entries[-1][2] != built:
                raise SystemExit(f'greedy {built} against optimum {best} on {docs}')
            cert = root / 'cert.bin'
            subprocess.run([bound, str(limit), str(budget), '400', str(built), str(listing), str(cert)],
                           check=True, stdout=subprocess.DEVNULL)
            lengths = B.eligible_at(docs, limit)
            checked = B.check(docs, lengths, cert, limit)
            if checked['lower_bound'] > best:
                raise SystemExit(f"bound {checked['lower_bound']} above optimum {best} on {docs}")
            gaps += best - checked['lower_bound']
            data = bytearray(cert.read_bytes())
            count = struct.unpack_from('<I', data, 12)[0]
            if count:
                struct.pack_into('<I', data, 20, 99)  # a price on a string that cannot exist
                bad = root / 'bad.bin'
                bad.write_bytes(data)
                try:
                    B.check(docs, lengths, bad, limit)
                except (SystemExit, IndexError, KeyError):
                    pass
                else:
                    raise SystemExit('a tampered certificate was accepted')
            tested += 1
    print(f'{tested} tiny corpora: greedy never below the optimum, bound never above it '
          f'(total slack {gaps}), tampered certificates refused')


if __name__ == '__main__':
    main()
