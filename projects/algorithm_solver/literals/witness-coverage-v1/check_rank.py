#!/usr/bin/env python3
"""Check the rank lower bounds and their matching dictionaries for matched80. Python 3.8+ and Git; no solver.

Map a string w to a vector over a prime field with one coordinate per character:
    v(w)[c] = sum of BASE**i over the positions i where w has character c.
Then v(xy) = v(x) + BASE**len(x) * v(y), so if a dictionary spells a string, the string's vector lies in
the span of the dictionary's vectors. A dictionary that spells a set of strings therefore has at least as
many entries as the rank of their vectors.

Unrestricted rule: the strings are the 80 programs. Rank 79, and a stored 79-entry dictionary rebuilds all 80.
Witness rule: a boundary whose two-character window occurs in fewer than two programs cannot lie inside a
legal multi-character entry, so every legal parse cuts there, and each block between cuts is spelled by
entries. The strings are those blocks. Rank 92, and the 92 single characters rebuild all 80.

    python3 -B check_rank.py /path/to/gamma [PRIME BASE]     (default 1000000007 2)
"""
import collections
import json
import subprocess
import sys

REPO = sys.argv[1]
P, B = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1_000_000_007, 2)
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'


def check(value, message):
    if not value:
        raise SystemExit('FAILED: ' + message)


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
manifest = json.loads(blob('scale-v2/generated/manifest.json'))['rows']


def rank(words, chars):
    rows = []
    for w in set(words):
        v, weight = [0] * len(chars), 1
        for c in w:
            v[chars[c]] = (v[chars[c]] + weight) % P
            weight = weight * B % P
        rows.append(v)
    r = 0
    for col in range(len(chars)):
        pivot = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inv = pow(rows[r][col], P - 2, P)
        rows[r] = [x * inv % P for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][col]:
                f = rows[i][col]
                rows[i] = [(x - f * y) % P for x, y in zip(rows[i], rows[r])]
        r += 1
    return r


def rebuilds(words, sources):
    """Number of sources that are a concatenation of the given words."""
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    count = 0
    for s in sources:
        reach = [False] * (len(s) + 1)
        reach[0] = True
        for i in range(len(s)):
            if reach[i]:
                for w in by_first.get(s[i], ()):
                    if s.startswith(w, i):
                        reach[i + len(w)] = True
        count += reach[len(s)]
    return count


STORED = {'compact': 'sixbit-v1/run-v1/a-u-compact', 'canonical': 'sixbit-v1/run-jupiter-v1/a-u-canonical'}
print(f'Field {P}, base {B}.')
for variant in ('compact', 'canonical'):
    sources = [blob('scale-v2/generated/' + r['file']) for r in manifest if r['variant'] == variant and r['id'] in wanted]
    check(len(sources) == 80 and len(set(sources)) == 80, variant + ': not 80 distinct sources')
    whole = set(sources)
    letters = sorted(set(b''.join(sources)))
    chars = {c: i for i, c in enumerate(letters)}

    # Unrestricted rule.
    program_rank = rank(sources, chars)
    vocabulary = [w.encode() for w in json.loads(blob(STORED[variant] + '/manifest.json'))['vocabulary']]
    check(len(set(vocabulary)) == len(vocabulary), variant + ': repeated entry in the stored dictionary')
    check(all(w and w not in whole and any(w in s for s in sources) for w in vocabulary), variant + ': ineligible stored entry')
    check(rebuilds(vocabulary, sources) == 80, variant + ': stored dictionary does not rebuild all 80')
    check(program_rank == len(vocabulary) == 79, variant + f': program rank {program_rank}, stored dictionary {len(vocabulary)}')

    # Witness rule.
    owners = collections.defaultdict(set)
    for n, s in enumerate(sources):
        for i in range(len(s) - 1):
            owners[s[i:i + 2]].add(n)
    blocks = []
    for s in sources:
        start = 0
        for i in range(len(s) - 1):
            if len(owners[s[i:i + 2]]) < 2:
                blocks.append(s[start:i + 1])
                start = i + 1
        blocks.append(s[start:])
    block_rank = rank(blocks, chars)
    singles = [bytes([c]) for c in letters]
    check(all(len(s) > 1 for s in sources), variant + ': a program is one character long')
    check(rebuilds(singles, sources) == 80, variant + ': single characters do not rebuild all 80')
    check(block_rank == len(letters) == 92, variant + f': block rank {block_rank}, alphabet {len(letters)}')

    print(f'{variant}: unrestricted minimum is 79 (program rank 79; the stored 79-entry dictionary rebuilds all 80).')
    print(f'{variant}: witness-rule minimum is 92 (rank of {len(set(blocks))} distinct forced blocks, {len(blocks)} with repeats, is 92; '
          f'the 92 single characters rebuild all 80).')
