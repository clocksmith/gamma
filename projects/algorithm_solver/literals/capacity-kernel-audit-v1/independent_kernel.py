#!/usr/bin/env python3
"""A second implementation of the rank-tight parsing test, written from the theorem statement and sharing no
code with capacity-diagnostic-v1. Witness rule, threshold 2, entries of at most 160 bytes. Python 3.8+.

    python3 -B independent_kernel.py      runs on the 35 real corpora and compares with the first implementation;
                                           writes independent-kernel.json; exits 1 on any disagreement

For a corpus: cut at forced boundaries, take the rank r of the blocks in each of two prime fields, and find
the free characters (unit vector outside the block space). A dictionary of r entries must cover every
occurrence of a free character with a multi-character entry whose vector is orthogonal to the kernel, and it
has at most k + delta such entries. If some such set spells every block that holds a free character, together
with the determined characters, the rank is attained (when the set has at most k entries, verified by replay).
If no such set exists, the minimum is at least r + 1.
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
FIELDS = ((1_000_000_007, 2), (998_244_353, 3))
CAP = 160


def reduced_rows(vectors, prime):
    """Reduced row echelon basis as {pivot column: row}."""
    basis = {}
    for raw in vectors:
        v = list(raw)
        for pivot, row in basis.items():
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % prime for a, b in zip(v, row)]
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inverse = pow(v[pivot], prime - 2, prime)
        v = [x * inverse % prime for x in v]
        for other, row in list(basis.items()):
            if row[pivot]:
                f = row[pivot]
                basis[other] = [(a - f * b) % prime for a, b in zip(row, v)]
        basis[pivot] = v
    return basis


def kernel_vectors(basis, width, prime):
    out = []
    for free in (j for j in range(width) if j not in basis):
        z = [0] * width
        z[free] = 1
        for pivot, row in basis.items():
            z[pivot] = (-row[free]) % prime
        out.append(z)
    return out


def forced_blocks(programs):
    owners = {}
    for n, p in enumerate(programs):
        for i in range(len(p) - 1):
            owners.setdefault(p[i:i + 2], set()).add(n)
    blocks = set()
    for p in programs:
        start = 0
        for i in range(len(p) - 1):
            if len(owners[p[i:i + 2]]) < 2:
                blocks.add(p[start:i + 1])
                start = i + 1
        blocks.add(p[start:])
    return sorted(blocks)


def spells(text, entries_by_first):
    reach = [True] + [False] * len(text)
    for i in range(len(text)):
        if reach[i]:
            for e in entries_by_first.get(text[i], ()):
                if text.startswith(e, i):
                    reach[i + len(e)] = True
    return reach[len(text)]


def test(programs, node_limit=200_000):
    letters = sorted(set(''.join(programs)))
    column = {c: n for n, c in enumerate(letters)}
    blocks = forced_blocks(programs)
    whole = set(programs)
    fields = []
    for prime, base in FIELDS:
        vectors = []
        for b in blocks:
            v, weight = [0] * len(letters), 1
            for c in b:
                v[column[c]] = (v[column[c]] + weight) % prime
                weight = weight * base % prime
            vectors.append(v)
        basis = reduced_rows(vectors, prime)
        fields.append((prime, base, len(basis), kernel_vectors(basis, len(letters), prime)))
    rank = max(f[2] for f in fields)
    attaining = [f for f in fields if f[2] == rank]
    d = len(letters) - rank
    if d == 0:
        return {'status': 'SATURATED', 'rank': rank, 'lowerBound': rank, 'dictionary': None}
    free = {letters[j] for _, _, _, kernel in attaining for z in kernel for j in range(len(letters)) if z[j]}
    determined = [c for c in letters if c not in free]
    k = len(free) - d

    # Eligible multi-character fragments that touch a free character and are orthogonal to the kernel in every attaining field.
    fragments = set()
    for n, p in enumerate(programs):
        others = [q for m, q in enumerate(programs) if m != n]
        free_positions = [i for i, c in enumerate(p) if c in free]
        starts = set()
        for q in free_positions:
            starts.update(range(max(0, q - CAP + 1), q + 1))
        for i in sorted(starts):
            sums = [[0] * len(kernel) for _, _, _, kernel in attaining]
            weights = [1] * len(attaining)
            touched = False
            for j in range(i, len(p)):
                c = p[j]
                for f, (prime, base, _, kernel) in enumerate(attaining):
                    col = column[c]
                    for z_index, z in enumerate(kernel):
                        sums[f][z_index] = (sums[f][z_index] + weights[f] * z[col]) % prime
                    weights[f] = weights[f] * base % prime
                touched = touched or c in free
                if j == i:
                    continue
                s = p[i:j + 1]
                if len(s.encode()) > CAP or not any(s in q for q in others):
                    break
                if touched and s not in whole and not any(any(row) for row in sums):
                    fragments.add(s)
    fragments = sorted(fragments)

    free_blocks = [b for b in blocks if any(c in free for c in b)]
    occurrence = {}
    for bi, b in enumerate(free_blocks):
        for pos, c in enumerate(b):
            if c in free:
                occurrence[(bi, pos)] = len(occurrence)
    covers = {}
    spans = [[False] * len(b) for b in free_blocks]
    for t in fragments:
        mask = 0
        for bi, b in enumerate(free_blocks):
            at = b.find(t)
            while at != -1:
                for pos in range(at, at + len(t)):
                    spans[bi][pos] = True
                    if (bi, pos) in occurrence:
                        mask |= 1 << occurrence[(bi, pos)]
                at = b.find(t, at + 1)
        covers[t] = mask

    # Slack: runs no fragment can cover, bounded by a block edge or a free character, need determined-only entries.
    covered_anywhere = {}
    for b in blocks:
        flags = [False] * len(b)
        for t in fragments:
            at = b.find(t)
            while at != -1:
                for pos in range(at, at + len(t)):
                    flags[pos] = True
                at = b.find(t, at + 1)
        covered_anywhere[b] = flags
    runs = set()
    for b in blocks:
        flags, i = covered_anywhere[b], 0
        while i < len(b):
            if flags[i]:
                i += 1
                continue
            j = i
            while j < len(b) and not flags[j]:
                j += 1
            if (i == 0 or b[i - 1] in free) and (j == len(b) or b[j] in free) and all(c not in free for c in b[i:j]):
                runs.add(b[i:j])
            i = j
    det_column = {c: n for n, c in enumerate(determined)}
    run_rank = 0
    for prime, base in FIELDS:
        vectors = []
        for run in runs:
            v, weight = [0] * len(determined), 1
            for c in run:
                v[det_column[c]] = (v[det_column[c]] + weight) % prime
                weight = weight * base % prime
            vectors.append(v)
        run_rank = max(run_rank, len(reduced_rows(vectors, prime)))
    delta = len(determined) - run_rank

    everything = (1 << len(occurrence)) - 1
    nodes = [0]

    def by_first(chosen):
        table = {}
        for e in list(determined) + chosen:
            table.setdefault(e[0], []).append(e)
        return table

    def search(need, chosen, limit):
        nodes[0] += 1
        if nodes[0] > node_limit:
            raise TimeoutError
        if need == 0:
            table = by_first(chosen)
            if all(spells(b, table) for b in free_blocks):
                return chosen
            if len(chosen) >= limit:
                return None
            for t in fragments:                                   # every extension is tried; nothing is pruned
                if t not in chosen:
                    found = search(0, chosen + [t], limit)
                    if found is not None:
                        return found
            return None
        if len(chosen) >= limit:
            return None
        best = None
        bit = 1
        while bit <= need:
            if need & bit:
                candidates = [t for t in fragments if covers[t] & bit and t not in chosen]
                if best is None or len(candidates) < len(best):
                    best = candidates
                    if not best:
                        return None
            bit <<= 1
        for t in best:
            found = search(need & ~covers[t], chosen + [t], limit)
            if found is not None:
                return found
        return None

    info = {'rank': rank, 'nullity': d, 'freeCharacters': len(free), 'k': k, 'delta': delta, 'fragments': len(fragments)}
    try:
        attained = search(everything, [], k)
        if attained is not None:
            return dict(info, status='RANK_ATTAINED', lowerBound=rank, dictionary=sorted(determined) + sorted(attained))
        if search(everything, [], k + delta) is None:
            return dict(info, status='RANK_UNATTAINABLE', lowerBound=rank + 1, dictionary=None)
    except TimeoutError:
        pass
    return dict(info, status='UNRESOLVED', lowerBound=rank, dictionary=None)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))
    import capped
    import evaluate as boundary
    rule = capped.Capped()
    first = load('diag', os.path.join(ROOT, 'capacity-diagnostic-v1', 'diagnostic.py'))
    sets = {'boundary/' + k: c['programs'] for k, c in boundary.load_instances().items()}
    independent = json.load(open(os.path.join(ROOT, 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')))['corpora']
    for k in ('C-1', 'C-2'):
        sets['independent/' + k] = independent[k]['programs']
    for folder, file_name, prefix in (('capacity-race-v1', 'boundary-instances.json', 'race/'), ('capacity-lagrangian-race-v1', 'public-instances.json', 'public/')):
        data = json.load(open(os.path.join(ROOT, folder, file_name)))
        data = data.get('corpora', data)
        for k, c in (data.items() if isinstance(data, dict) else [(c.get('corpusId') or c.get('id'), c) for c in data]):
            if isinstance(c, dict) and 'programs' in c:
                sets[prefix + k] = c['programs']
    out, disagreements = {}, []
    for name, programs in sets.items():
        started = time.time()
        mine = test(programs)
        theirs = first.nullspace_kernel_certificate(programs, 2)
        replay = None if mine['dictionary'] is None else (rule.dictionary_spells(programs, mine['dictionary']) and len(mine['dictionary']) == mine['rank'])
        agree = mine['status'] == theirs['status'] and mine['rank'] == theirs['rank'] and mine['lowerBound'] == theirs['certifiedLowerBound']
        if not agree or replay is False:
            disagreements.append(name)
        out[name] = {'alphabet': len(set(''.join(programs))), 'status': mine['status'], 'rank': mine['rank'], 'lowerBound': mine['lowerBound'],
                     'dictionaryEntries': None if mine['dictionary'] is None else len(mine['dictionary']), 'dictionaryReplays': replay,
                     'firstImplementation': theirs['status'], 'agree': agree}
        print(f"{name:18} alphabet {out[name]['alphabet']:3} rank {mine['rank']:3} {mine['status']:18} bound {mine['lowerBound']:3} replay {str(replay):>5} "
              f"first implementation {theirs['status']:18} {'agree' if agree else 'DISAGREE'} {time.time() - started:6.1f} s", flush=True)
    with open(os.path.join(HERE, 'independent-kernel.json'), 'w') as f:
        json.dump({'schema': 'capacity-kernel-audit-independent/v1', 'corpora': out, 'disagreements': disagreements}, f, indent=1)
        f.write('\n')
    print(len(out), 'corpora;', len(disagreements), 'disagreements')
    sys.exit(1 if disagreements else 0)


if __name__ == '__main__':
    main()
