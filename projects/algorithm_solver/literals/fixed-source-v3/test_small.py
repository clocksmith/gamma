#!/usr/bin/env python3
"""Synthetic gates for fixed-source-v3. Touches no real corpus.

    test_small.py <engine> [--lp]
"""
import itertools
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import encoded as X
import verify as V

BINDING = {'manifest': 'm' * 64, 'impl': 'i' * 64, 'run': 'fixture', 'cuts': {'both': 'c' * 64}}


def receipt(cuts='none'):
    return f"manifest={BINDING['manifest']} pool=both cuts={cuts} impl={BINDING['impl']} run=fixture"


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


def legal(docs, groups, limit, policy, entries):
    _, units = V.build_views(docs, groups, b'', False, policy)
    return not refused(lambda: V.check_entries(rows(*entries), docs, units, limit, policy))


def write_list(root, docs):
    paths = []
    for index, raw in enumerate(docs):
        path = root / f'd{index}.txt'
        path.write_bytes(raw)
        paths.append(str(path))
    listing = root / 'list.txt'
    listing.write_text('\n'.join(paths) + '\n')
    return listing


def run_engine(engine, mode, policy, limit, budget, listing, out, seed=None, groups=None, cuts=None, cut_tag='none'):
    env = {**os.environ, 'FSV3_RECEIPT': receipt(cut_tag)}
    env.pop('FSV3_GROUPS', None)
    env.pop('FSV3_CUTS', None)
    if groups:
        env['FSV3_GROUPS'] = str(groups)
    if cuts:
        env['FSV3_CUTS'] = str(cuts)
    command = [engine, mode, policy, str(limit), str(budget), '30', str(listing), str(out)] + ([str(seed)] if seed else [])
    subprocess.run(command, check=True, env=env)


def policy_gates():
    # One problem's two files satisfy a two-file rule but not a two-problem rule.
    docs = [b'uniquezz', b'other', b'uniquezz!', b'things']
    groups = [0, 1, 0, 1]
    assert legal(docs, groups, 8, 's2-nowhole', [b'unique'])
    assert not legal(docs, groups, 8, 'p2-nowhole', [b'unique'])
    docs = [b'abcx', b'abcy', b'qqqq', b'rrrr']
    assert legal(docs, [0, 1, 0, 1], 3, 'p2-nowhole', [b'abc'])
    assert not legal(docs, [0, 0, 1, 1], 3, 'p2-nowhole', [b'abc'])


def cut_gates(engine, root):
    docs = [b'abab', b'abcd']
    listing = write_list(root, docs)
    cuts = bytes([0, 0, 1, 0, 0, 0, 1, 0])
    cut_file = root / 'cuts.bin'
    cut_file.write_bytes(cuts)
    chain = root / 'cut-chain.txt'
    run_engine(engine, 'greedy-entry', 's1-whole', 4, 8, listing, chain, cuts=cut_file, cut_tag=BINDING['cuts']['both'])
    built = V.read_chain(chain)
    assert built[0]['cuts'] == BINDING['cuts']['both']
    segments, _ = V.build_views(docs, [0, 1], cuts, True, 's1-whole')
    assert segments == [[b'ab', b'ab'], [b'ab', b'cd']]
    root_trie = {}
    for row in built[1]:
        assert len(row[4]) <= 2
        V.insert(root_trie, row[4])
    assert V.score(docs, segments, root_trie)[0] == 2
    # A whole-file entry cannot be used across a forbidden boundary.
    whole = {}
    for entry in (b'a', b'b', b'c', b'd', b'abab'):
        V.insert(whole, entry)
    assert V.score([b'abab'], [[b'ab', b'ab']], whole) == (1, 4)
    assert V.score([b'abab'], [[b'abab']], whole) == (1, 1)
    assert refused(lambda: V.check_receipt(built[0], 's1-whole', 'greedy-entry', 4, 'both', None, BINDING))


def receipt_gates(engine, root):
    listing = write_list(root, [b'abab', b'abcd'])
    chain = root / 'gate.txt'
    run_engine(engine, 'greedy-entry', 's1-whole', 2, 8, listing, chain)
    head = V.read_chain(chain)[0]
    V.check_receipt(head, 's1-whole', 'greedy-entry', 2, 'both', None, BINDING)
    assert refused(lambda: V.check_receipt(head, 's2-nowhole', 'greedy-entry', 2, 'both', None, BINDING))
    assert refused(lambda: V.check_receipt(head, 's1-whole-cuts', 'greedy-entry', 2, 'both', None, BINDING))
    text = chain.read_text()
    broken = root / 'broken.txt'
    broken.write_text(text.replace(' cuts=none', ''))
    assert refused(lambda: V.read_chain(broken))
    env = {k: v for k, v in os.environ.items() if k != 'FSV3_RECEIPT'}
    assert subprocess.run([engine, 'greedy-entry', 's1-whole', '2', '8', '10', str(listing), str(chain)], env=env,
                          capture_output=True).returncode != 0


def huffman_gates():
    rng = random.Random(11)
    for _ in range(300):
        counts = [rng.randint(1, 30) for _ in range(rng.randint(2, 7))]
        assert X.huffman_bits(counts) == brute_prefix(counts)
    assert X.huffman_bits([9]) == 9
    assert X.huffman_bits([]) == 0
    assert X.fixed_bits(10, 8) == 30 and X.fixed_bits(10, 9) == 40


def brute_prefix(counts):
    """The optimal prefix-code cost, by trying every merge order."""
    if len(counts) == 1:
        return 0
    best = None
    for i, j in itertools.combinations(range(len(counts)), 2):
        rest = [c for k, c in enumerate(counts) if k not in (i, j)]
        merged = counts[i] + counts[j]
        value = merged + brute_prefix(rest + [merged])
        best = value if best is None else min(best, value)
    return best


def pathpiece_gates(engine, root):
    docs = [b'the cat sat', b'the cat ran', b'a cat sat here']
    listing = write_list(root, docs)
    seed = root / 'seed.txt'
    seed.write_text('\n'.join(entry.hex() for entry in (b'the', b'cat', b' cat', b'sat', b'the ', b' s')) + '\n')
    chain = root / 'path.txt'
    run_engine(engine, 'pathpiece', 's1-whole', 4, 64, listing, chain, seed=seed)
    head, entries, _, _, done, _ = V.read_chain(chain)
    assert head['mode'] == 'pathpiece' and done['stopped'] == '0'
    V.check_framing(entries)
    alphabet = len({b for raw in docs for b in raw})
    assert all(len(row[4]) == 1 for row in entries[:alphabet]) and len(entries) == alphabet + 6
    previous = None
    for size in range(alphabet, len(entries) + 1):
        trie = {}
        for row in entries[:size]:
            V.insert(trie, row[4])
        spelled, tokens = V.score(docs, [[raw] for raw in docs], trie)
        assert spelled == len(docs)
        assert previous is None or tokens <= previous
        previous = tokens


def greedtok_replay(docs, candidates, built):
    """Checks each engine pick against Algorithms 1 to 3 of Lim et al., written from the paper."""
    state = [[0] * (len(raw) - 1) for raw in docs]

    def can(m, i, size):
        return (i == 0 or m[i - 1] == 0) and (i + size == len(m) + 1 or m[i + size - 1] == 0)

    def occurrences(token):
        for d, raw in enumerate(docs):
            for i in range(len(raw) - len(token) + 1):
                if raw[i:i + len(token)] == token:
                    yield d, i

    def score(token):
        copy = [list(m) for m in state]
        total = 0
        for d, i in occurrences(token):
            if can(copy[d], i, len(token)):
                total += sum(copy[d][j] == 0 for j in range(i, i + len(token) - 1))
                for j in range(i, i + len(token) - 1):
                    copy[d][j] = 1
        return total

    chosen = set()
    for token in built:
        best = max(score(t) for t in candidates if t not in chosen)
        assert best > 0 and score(token) == best, (docs, token, score(token), best)
        chosen.add(token)
        for d, i in occurrences(token):
            if can(state[d], i, len(token)):
                for j in range(i, i + len(token) - 1):
                    state[d][j] = 1
    remaining = [score(t) for t in candidates if t not in chosen]
    return max(remaining, default=0)


def greedtok_gates(engine, root):
    rng = random.Random(7)
    tested = 0
    while tested < 30:
        docs = list({bytes(rng.choice(b'ab') for _ in range(rng.randint(4, 8))) for _ in range(3)})
        if len(docs) < 3:
            continue
        candidates = {raw[i:i + size] for raw in docs for size in range(2, 5) for i in range(len(raw) - size + 1)}
        alphabet = len({b for raw in docs for b in raw})
        listing = write_list(root, docs)
        chain = root / 'greedtok.txt'
        run_engine(engine, 'greedtok', 's1-whole', 4, alphabet + 3, listing, chain)
        entries = V.read_chain(chain)[1]
        built = [row[4] for row in entries[alphabet:]]
        left = greedtok_replay(docs, candidates, built)
        assert len(built) == 3 or left == 0, (docs, built, left)
        trie = {}
        for row in entries:
            V.insert(trie, row[4])
        assert V.score(docs, [[raw] for raw in docs], trie)[0] == len(docs)
        tested += 1
    return tested


def lp_gates():
    import solve_lp as L
    rng = random.Random(5)
    checked = 0
    while checked < 12:
        docs = list({bytes(rng.choice(b'abc') for _ in range(rng.randint(3, 5))) for _ in range(3)})
        if len(docs) < 3:
            continue
        for policy in ('s1-whole', 's2-nowhole'):
            strings = L.eligible(docs, 3, policy)[0]
            if len(strings) > 12:
                continue
            alphabet = len({b for raw in docs for b in raw})
            budget = alphabet + 1
            lp, names = L.build(docs, 3, budget, policy)
            solver = L.highspy.Highs()
            solver.setOptionValue('output_flag', False)
            solver.passModel(lp)
            solver.run()
            value = solver.getInfo().objective_function_value
            best = None
            for size in range(1, budget + 1):
                for subset in itertools.combinations(names, size):
                    trie = {}
                    for entry in subset:
                        V.insert(trie, entry)
                    spelled, tokens = V.score(docs, [[raw] for raw in docs], trie)
                    if spelled == len(docs) and (best is None or tokens < best):
                        best = tokens
            assert best is not None and value <= best + 1e-6, (docs, policy, value, best)
            rounded = L.rounded(names, solver.getSolution().col_value, budget, False)
            assert len(rounded) <= budget
            checked += 1
    return checked


def main():
    engine = sys.argv[1]
    policy_gates()
    huffman_gates()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        receipt_gates(engine, root)
        cut_gates(engine, root)
        pathpiece_gates(engine, root)
        tested = greedtok_gates(engine, root)
    message = f'gates passed; GreedTok reference on {tested} tiny corpora'
    if '--lp' in sys.argv:
        message += f'; LP at or below brute force on {lp_gates()} tiny instances'
    print(message)


if __name__ == '__main__':
    main()
