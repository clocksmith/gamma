#!/usr/bin/env python3
"""Checks of the format library on small hand-made inputs. Standard library only."""
import itertools
import random

import bits_oh as B


def brute_min_tokens(raw, entries, singles):
    n = len(raw)
    best = [None] * (n + 1)
    best[0] = 0
    for j in range(1, n + 1):
        opts = []
        for e in entries:
            i = j - len(e)
            if i >= 0 and best[i] is not None and raw[i:j] == e:
                opts.append(best[i] + 1)
        if bytes([raw[j - 1]]) not in singles and best[j - 1] is not None:
            opts.append(best[j - 1] + 1)  # escape
        best[j] = min(opts) if opts else None
    return best[n]


def test_varint():
    for v in (0, 1, 127, 128, 300, 16383, 16384, 2 ** 31):
        enc = B.varint(v)
        assert B.read_varint(enc, 0) == (v, len(enc))


def test_huffman_is_optimal_on_small_cases():
    rng = random.Random(7)
    for _ in range(200):
        counts = [rng.randint(1, 40) for _ in range(rng.randint(2, 7))]
        got = sum(c * l for c, l in zip(counts, B.huffman_lengths(counts)))
        # brute force over all length assignments with Kraft sum <= 1
        best = None
        for ls in itertools.product(range(1, len(counts)), repeat=len(counts)):
            if sum(2.0 ** -l for l in ls) <= 1.0 + 1e-12:
                c = sum(a * b for a, b in zip(counts, ls))
                best = c if best is None or c < best else best
        assert got == best, (counts, got, best)


def test_abc_needs_a_tiling_not_just_coverage():
    # {ab, bc} matches over every position of abc but cannot tile it; with the
    # escape the parse must spend an escape, not report a clean parse.
    d = B.Dictionary([b'ab', b'bc'])
    edges = d.edges(b'abc')
    syms = B.parse_tokens(edges)
    assert len(syms) == 2 and syms.count(d.ESC) == 1


def test_parsers_match_brute_force_and_round_trip():
    rng = random.Random(11)
    alphabet = b'abcd'
    for _ in range(300):
        singles = [bytes([c]) for c in alphabet if rng.random() < 0.8]
        multi = set()
        while len(multi) < rng.randint(0, 6):
            multi.add(bytes(rng.choice(alphabet) for _ in range(rng.randint(2, 4))))
        entries = singles + sorted(multi)
        d = B.Dictionary(entries)
        files = [bytes(rng.choice(alphabet + b'z') for _ in range(rng.randint(0, 24))) for _ in range(rng.randint(1, 4))]
        edges = [d.edges(f) for f in files]
        for f, e in zip(files, edges):
            assert len(B.parse_tokens(e)) == brute_min_tokens(f, entries, set(singles))
        lengths, counts, bits, _ = B.fit_table(d, edges)
        parses = []
        total = 0
        for e in edges:
            syms, c = B.parse_bits(e, lengths, d.ESC)
            parses.append(syms)
            total += c + lengths[d.EOF]
        payload, per_file = B.encode_payload(d, lengths, files, parses)
        assert sum(per_file) == total and len(payload) == (total + 7) // 8
        archive = B.build_header(entries, lengths) + B.varint(len(files)) + payload
        assert B.decode_archive(archive) == files
        # removing an entry can never lower the minimum bit cost
        for s in range(d.n):
            if len(entries[s]) > 1:
                for e in edges:
                    assert B.parse_bits(e, lengths, d.ESC, banned=s)[1] >= B.parse_bits(e, lengths, d.ESC)[1]


def test_header_round_trip():
    entries = [b'a', b'b', b'ab', b'\x00\xff']
    lengths = [1, 2, 3, 4, 5, 5]
    h = B.build_header(entries, lengths)
    assert B.parse_header(h) == (entries, lengths, len(h))


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
