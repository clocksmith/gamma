#!/usr/bin/env python3
"""Proved limits on fixed-source-v1, computed from the sources alone.

1. Rank: every dictionary that spells all files of a corpus under the entry rule
   has at least as many entries as the rank of its forced blocks (two primes).
2. Reachability: a file with no parse into eligible entries of 2..L bytes cannot
   be spelled by any no-singleton dictionary.

    check_limits.py <private folder> <output json>
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMES = ((1_000_000_007, 2), (998_244_353, 3))
LENGTHS = (2, 4, 8, 16, 32, 64)


def corpus(private):
    rows = json.loads((HERE / 'manifest.json').read_text())['problems']
    files = {}
    for language, extension in (('python', 'py'), ('javascript', 'js')):
        docs = []
        for row in rows:
            raw = (private / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit('hash mismatch')
            docs.append(raw)
        files[language] = docs
    files['both'] = files['python'] + files['javascript']
    return files


def forced_blocks(docs):
    """Split at every adjacent pair that occurs in fewer than two files."""
    seen = {}
    for index, raw in enumerate(docs):
        for at in range(len(raw) - 1):
            pair = raw[at:at + 2]
            mark = seen.get(pair)
            if mark is None:
                seen[pair] = index
            elif mark != index:
                seen[pair] = -1
    blocks = set()
    for raw in docs:
        start = 0
        for at in range(1, len(raw)):
            if seen[raw[at - 1:at + 1]] != -1:
                blocks.add(raw[start:at])
                start = at
        blocks.add(raw[start:])
    return blocks


def rank(blocks, alphabet, prime, base):
    place = {c: i for i, c in enumerate(alphabet)}
    size = len(alphabet)
    pivots = {}
    for block in sorted(blocks, key=lambda b: (len(b), b)):
        vector = [0] * size
        power = 1
        for byte in block:
            at = place[byte]
            vector[at] = (vector[at] + power) % prime
            power = power * base % prime
        for column in range(size):
            if not vector[column]:
                continue
            pivot = pivots.get(column)
            if pivot is None:
                inverse = pow(vector[column], -1, prime)
                pivots[column] = [v * inverse % prime for v in vector]
                break
            factor = vector[column]
            vector = [(v - factor * p) % prime for v, p in zip(vector, pivot)]
        if len(pivots) == size:
            break
    return len(pivots)


def eligible(docs, limit):
    """Strings of 2..limit bytes in at least two files, not a whole file."""
    whole = set(docs)
    allowed = set()
    alive = None
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


def reachable(raw, allowed, limit):
    size = len(raw)
    can = bytearray(size + 1)
    can[0] = 1
    for start in range(size):
        if not can[start]:
            continue
        for length in range(2, min(limit, size - start) + 1):
            if raw[start:start + length] in allowed:
                can[start + length] = 1
    return bool(can[size])


def main():
    private, output = Path(sys.argv[1]), Path(sys.argv[2])
    files = corpus(private)
    result = {'schema': 'gamma.fixed-source-limits.v1', 'corpora': {}}
    for name, docs in files.items():
        alphabet = sorted(set(b''.join(docs)))
        blocks = forced_blocks(docs)
        ranks = [rank(blocks, alphabet, p, b) for p, b in PRIMES]
        entry = {'files': len(docs), 'bytes': sum(map(len, docs)), 'alphabet': len(alphabet),
                 'forced_blocks': len(blocks), 'block_rank': ranks,
                 'minimum_entries_lower_bound': max(ranks), 'no_singleton': {}}
        for limit in LENGTHS:
            allowed = eligible(docs, limit)
            spellable = sum(reachable(raw, allowed, limit) for raw in docs)
            entry['no_singleton'][str(limit)] = {'spellable_files': spellable,
                                                 'proved_unspellable': len(docs) - spellable}
        result['corpora'][name] = entry
        print(name, entry['alphabet'], ranks, {k: v['spellable_files'] for k, v in entry['no_singleton'].items()}, flush=True)
    output.write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
