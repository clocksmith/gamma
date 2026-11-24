#!/usr/bin/env python3
"""Synthetic gates for fixed-source-v2. Touches no real corpus.

    test_small.py <engine> <bound>
"""
import itertools
import os
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_bound as B
import check_limits as C
import verify as V

BINDING = {'manifest': 'm' * 64, 'impl': 'i' * 64, 'run': 'fixture'}
RECEIPT = f"manifest={BINDING['manifest']} pool=both impl={BINDING['impl']} run=fixture"
POLICIES = ('s1-whole', 's1-nowhole', 's2-nowhole')


def rows(*entries):
    out, stored = [], 0
    for index, entry in enumerate(entries):
        stored += 1 + len(entry)
        out.append((index + 1, stored, -1, 0, entry))
    return out


def refused(action):
    try:
        action()
    except V.Rejected:
        return True
    return False


def legal(docs, limit, policy, entries, singles=True):
    return not refused(lambda: V.check_entries(rows(*entries), docs, limit, policy, singles))


def gates():
    # A substring repeated within one file only.
    docs = [b'abcabc', b'xyz']
    assert legal(docs, 3, 's1-whole', [b'abc'])
    assert legal(docs, 3, 's1-nowhole', [b'abc'])
    assert not legal(docs, 3, 's2-nowhole', [b'abc'])

    # A multibyte entry that is a whole file and a substring of another file.
    docs = [b'abc', b'zabcz']
    assert legal(docs, 3, 's1-whole', [b'abc'])
    assert not legal(docs, 3, 's1-nowhole', [b'abc'])
    assert not legal(docs, 3, 's2-nowhole', [b'abc'])

    # The same verified bytes fail the historical control and pass the primary.
    docs = [b'hello!', b'world?']
    dictionary = [b'hello!', b'world?']
    root = {}
    for entry in dictionary:
        V.insert(root, entry)
    assert V.score(docs, root)[:2] == (2, 2)
    assert legal(docs, 6, 's1-whole', dictionary)
    assert not legal(docs, 6, 's2-nowhole', dictionary)

    # Length limit: at the limit passes, one over fails.
    assert legal([b'abcd'], 3, 's1-whole', [b'abc'])
    assert not legal([b'abcd'], 3, 's1-whole', [b'abcd'])

    # Entry and byte budgets, below and at the cap.
    chain = rows(b'a', b'bc', b'def')  # stored 2, 5, 9
    assert V.prefix_for(chain, 2, None) == 2 and V.prefix_for(chain, 3, None) == 3
    assert V.prefix_for(chain, 3, 8) == 2 and V.prefix_for(chain, 3, 9) == 3

    # Two dictionaries pay four routing bytes against the same cap.
    assert 5 + 4 + 4 > 12 and 4 + 4 + 4 <= 12

    # Mode, membership and duplicates.
    assert not legal([b'ab'], 2, 's1-whole', [b'a'], singles=False)
    assert legal([b'ab'], 2, 's1-whole', [b'ab'], singles=False)
    assert not legal([b'ab'], 2, 's1-whole', [b'c'])
    assert not legal([b'ab'], 2, 's1-whole', [b'zz'])
    assert not legal([b'ab'], 2, 's1-whole', [b'a', b'a'])

    # One corrupted intermediate stored length is refused.
    bad = rows(b'a', b'bc', b'def')
    bad[1] = (bad[1][0], bad[1][1] + 1, *bad[1][2:])
    assert refused(lambda: V.check_framing(bad))
    assert not refused(lambda: V.check_framing(rows(b'a', b'bc', b'def')))

    # Reachability with every eligible string is not one budgeted dictionary.
    docs = [b'abcd', b'efgh', b'ijkl']
    whole, sizes = set(docs), set(map(len, docs))
    assert all(C.reachable(raw, 2, 's1-whole', whole, sizes, None) for raw in docs)
    needed = {raw[i:i + 2] for raw in docs for i in (0, 2)}
    assert len(needed) == 6
    root = {}
    for entry in sorted(needed)[:5]:
        V.insert(root, entry)
    assert V.score(docs, root)[0] == 2

    # The closed-form reachability identity against the graph.
    for size in range(2, 40):
        raw = bytes(range(size))
        for limit in (2, 3, 4):
            assert C.reachable(raw, limit, 's1-whole', {raw}, {size}, None) == C.identity(raw, limit)
    assert not C.identity(b'x', 2)


def binding_gates(engine, root):
    (root / 'a.txt').write_bytes(b'abab')
    (root / 'b.txt').write_bytes(b'abcd')
    listing = root / 'gate.txt'
    listing.write_text(f"{root / 'a.txt'}\n{root / 'b.txt'}\n")
    chain = root / 'gate-chain.txt'
    env = {**os.environ, 'FSV2_RECEIPT': RECEIPT}
    subprocess.run([engine, 'greedy-entry', 's1-whole', '2', '8', '10', str(listing), str(chain)], check=True, env=env)
    receipt = V.read_chain(chain)[0]
    V.check_receipt(receipt, 's1-whole', 'greedy-entry', 2, 'both', None, BINDING)
    assert refused(lambda: V.check_receipt(receipt, 's2-nowhole', 'greedy-entry', 2, 'both', None, BINDING))
    assert refused(lambda: V.check_receipt(receipt, 's1-whole', 'greedy-entry', 2, 'python', None, BINDING))
    assert refused(lambda: V.check_receipt(receipt, 's1-whole', 'greedy-entry', 2, 'both', None,
                                           {**BINDING, 'manifest': 'x' * 64}))
    text = chain.read_text()
    missing = root / 'gate-missing.txt'
    missing.write_text(text.replace(' run=fixture', ''))
    assert refused(lambda: V.read_chain(missing))
    doubled = root / 'gate-doubled.txt'
    doubled.write_text(text.replace(' run=fixture', ' run=fixture run=other'))
    assert refused(lambda: V.read_chain(doubled))
    unbound = subprocess.run([engine, 'greedy-entry', 's1-whole', '2', '8', '10', str(listing), str(chain)],
                             env={k: v for k, v in os.environ.items() if k != 'FSV2_RECEIPT'}, capture_output=True)
    assert unbound.returncode != 0


def eligible(docs, limit, policy):
    least, keep_whole = V.POLICIES[policy]
    whole = set(docs)
    found = {bytes([b]) for raw in docs for b in raw}
    for raw in docs:
        for length in range(2, limit + 1):
            for at in range(len(raw) - length + 1):
                piece = raw[at:at + length]
                if (keep_whole or piece not in whole) and sum(piece in other for other in docs) >= least:
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
        assert b''.join(pieces) == raw
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


def race(engine, bound, root):
    rng = random.Random(20261123)
    env = {**os.environ, 'FSV2_RECEIPT': RECEIPT}
    tested = {policy: 0 for policy in POLICIES}
    slack = 0
    while min(tested.values()) < 40:
        docs = list({bytes(rng.choice(b'abc') for _ in range(rng.randint(3, 6))) for _ in range(rng.randint(3, 4))})
        if len(docs) < 3:
            continue
        limit = 3
        alphabet = len({b for raw in docs for b in raw})
        paths = []
        for index, raw in enumerate(docs):
            path = root / f'{index}.txt'
            path.write_bytes(raw)
            paths.append(str(path))
        listing = root / 'list.txt'
        listing.write_text('\n'.join(paths) + '\n')
        for policy in POLICIES:
            if tested[policy] >= 40:
                continue
            candidates = eligible(docs, limit, policy)
            if len(candidates) > 13 or len(candidates) <= alphabet:
                continue
            budget = alphabet + rng.randint(0, 2)
            best = optimum(docs, candidates, budget)
            chain = root / 'chain.txt'
            subprocess.run([engine, 'greedy-entry', policy, str(limit), str(budget), '30', str(listing), str(chain)],
                           check=True, env=env)
            _, entries, _, _, _ = V.read_chain(chain)
            V.check_framing(entries)
            V.check_entries(entries, docs, limit, policy, True)
            built = cost(docs, [row[4] for row in entries])
            assert built is not None and built >= best and entries[-1][2] == built
            cert = root / 'cert.bin'
            subprocess.run([bound, policy, str(limit), str(budget), '400', str(built), str(listing), str(cert)],
                           check=True, stdout=subprocess.DEVNULL)
            lengths = B.eligible_at(docs, limit, policy)
            checked = B.check(docs, lengths, cert, limit, policy)
            assert checked['lower_bound'] <= best, (docs, policy, checked['lower_bound'], best)
            slack += best - checked['lower_bound']
            data = bytearray(cert.read_bytes())
            if struct.unpack_from('<I', data, 16)[0]:
                struct.pack_into('<I', data, 24, 99)
                bad = root / 'bad.bin'
                bad.write_bytes(data)
                try:
                    B.check(docs, lengths, bad, limit, policy)
                except (SystemExit, IndexError, KeyError):
                    pass
                else:
                    raise AssertionError('a tampered certificate was accepted')
                data = bytearray(cert.read_bytes())
                other = POLICIES[(POLICIES.index(policy) + 1) % 3]
                wrong = root / 'wrong.bin'
                wrong.write_bytes(data)
                try:
                    B.check(docs, lengths, wrong, limit, other)
                except SystemExit:
                    pass
                else:
                    raise AssertionError('a certificate was accepted under another policy')
            tested[policy] += 1
    return tested, slack


def main():
    engine, bound = sys.argv[1], sys.argv[2]
    gates()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        binding_gates(engine, root)
        tested, slack = race(engine, bound, root)
    print(f'gates passed; brute-force corpora by policy {tested}: greedy never below the optimum, '
          f'bound never above it (total slack {slack}), tampered and wrong-policy certificates refused')


if __name__ == '__main__':
    main()
