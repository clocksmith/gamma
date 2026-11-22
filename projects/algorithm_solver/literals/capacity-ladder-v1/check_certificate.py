#!/usr/bin/env python3
"""Independent check of a defect-tree certificate from ladder.py. It shares no code with ladder.py: blocks, rank
and eligible entries come from capacity-boundary-v1 (evaluate.py and the capped checker), and the arithmetic
is redone here. Python 3.10+; no numpy, no solver. Witness rule only.

What a certificate says. Z is a basis of the vectors orthogonal to every block vector, in the prime field given,
so it has (alphabet - rank) rows. For an entry t, phi(t) = Z v(t). Any dictionary D that spells the blocks spans
the block space, so the space Phi(D) spanned by its phi-vectors has dimension at most |D| - rank.

A node (space, spare, block, position) claims: no dictionary has Phi(D) containing `space` and dimension at most
dim(space) + spare. The check, for every eligible entry e that covers that position of that block (the single
character, and every eligible substring of the block through it):
  * phi(e) must lie outside `space`. D covers the position with one of these entries, so Phi(D) is larger.
  * With spare = 0 that already contradicts the dimension. With spare > 0, space + <phi(e)> must be the space of
    one of the node's children, which carries spare - 1.
The root has the zero space and spare = refutes - rank, so the tree shows no dictionary of `refutes` entries exists.

    check(programs, certificate) -> the certified lower bound; raises ValueError when the certificate is not valid.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'capacity-boundary-v1'))
import capped                                   # noqa: E402
import evaluate as boundary                     # noqa: E402


def echelon(rows, prime):
    """Reduced row echelon form as a sorted tuple of rows; the canonical name of the space the rows span."""
    basis = []
    for raw in rows:
        v = [x % prime for x in raw]
        for row in basis:
            pivot = next(i for i, x in enumerate(row) if x)
            if v[pivot]:
                k = v[pivot]
                v = [(a - k * b) % prime for a, b in zip(v, row)]
        pivot = next((i for i, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inverse = pow(v[pivot], prime - 2, prime)
        v = [x * inverse % prime for x in v]
        basis = [[(a - row[pivot] * b) % prime for a, b in zip(row, v)] if row[pivot] else row for row in basis]
        basis.append(v)
    return tuple(sorted(tuple(row) for row in basis))


def check(programs, certificate):
    c = certificate
    if c.get('schema') != 'bits-defect-tree/v1' or c.get('rule') != 'W2':
        raise ValueError('not a witness-rule defect-tree certificate')
    prime, base, letters, kernel = c['prime'], c['base'], c['letters'], c['kernel']
    if sorted(set(''.join(programs))) != letters:
        raise ValueError('the alphabet differs')
    column = {ch: n for n, ch in enumerate(letters)}

    def vector(text):
        v, weight = [0] * len(letters), 1
        for ch in text:
            v[column[ch]] = (v[column[ch]] + weight) % prime
            weight = weight * base % prime
        return v

    blocks = set(boundary.forced_blocks(programs))
    rank = boundary.rank(sorted(blocks), prime, base)
    if len(kernel) != len(letters) - rank or len(echelon(kernel, prime)) != len(kernel):
        raise ValueError('the kernel basis does not have alphabet - rank independent rows')
    for b in blocks:
        v = vector(b)
        if any(sum(x * y for x, y in zip(z, v)) % prime for z in kernel):
            raise ValueError('a kernel row is not orthogonal to a block')

    phi_char = {ch: [z[column[ch]] % prime for z in kernel] for ch in letters}
    prefixes = {}

    def prefix(block):
        """prefix(block)[i] = sum over k < i of base^k phi(block[k]). phi(block[a:b]) is (prefix[b] - prefix[a]) / base^a,
        and a non-zero factor does not change which space a vector spans, so the difference is used as it is."""
        if block not in prefixes:
            rows, current, weight = [[0] * len(kernel)], [0] * len(kernel), 1
            for ch in block:
                current = [(x + weight * y) % prime for x, y in zip(current, phi_char[ch])]
                weight = weight * base % prime
                rows.append(current)
            prefixes[block] = rows
        return prefixes[block]

    whole = set(programs)
    eligible = {programs[n][i:j] for n, i, j in capped.Capped().occurrences(programs)}
    nodes = c['nodes']
    if not nodes or nodes[0]['space'] or nodes[0]['spare'] != c['refutes'] - rank or nodes[0]['spare'] < 0:
        raise ValueError('the root is not the zero space with spare = refutes - rank')
    for n, node in enumerate(nodes):
        space, spare, block, position = echelon(node['space'], prime), node['spare'], node['block'], node['position']
        if block not in blocks or not 0 <= position < len(block):
            raise ValueError(f'node {n}: not a position of a block')
        children = {}
        for child in node['children']:
            if nodes[child]['spare'] != spare - 1:
                raise ValueError(f'node {n}: a child does not carry spare - 1')
            children[echelon(nodes[child]['space'], prime)] = child
        rows, seen = prefix(block), set()
        spans = [(a, b) for a in range(position + 1) for b in range(position + 1, len(block) + 1) if b - a > 1 and block[a:b] in eligible]
        if block[position] not in whole:
            spans.append((position, position + 1))
        for a, b in spans:
            vector_phi = tuple((x - y) % prime for x, y in zip(rows[b], rows[a]))
            if vector_phi in seen:
                continue
            seen.add(vector_phi)
            bigger = echelon(list(space) + [vector_phi], prime)
            if bigger == space:
                raise ValueError(f'node {n}: the entry {block[a:b]!r} covers the position and lies inside the space')
            if spare > 0 and bigger not in children:
                raise ValueError(f'node {n}: the entry {block[a:b]!r} leads to a space that is not a child')
    return c['refutes'] + 1


if __name__ == '__main__':
    import json
    instance, certificate = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    print('certified lower bound', check(instance['programs'], certificate))
