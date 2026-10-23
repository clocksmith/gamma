"""Supplied-text fraction-flow prototype; no corpus loader or run entry point."""
import importlib.util
import hashlib
import os
from pathlib import Path
import time

import numpy as np
from scipy.sparse import coo_matrix, vstack

if not __debug__ or 'PYTHONOPTIMIZE' in os.environ:
    raise RuntimeError('Normal assertion checks required')

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('fraction_repair_seeded_solver', HERE.parent / 'seeded-repair-v1/model.py')
backend = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backend)


def word_cost(word):
    assert word
    return 9 if len(word) == 1 else -1


def exact(texts, vocab):
    """Independent sliced-string DP; ties are (F, N, entry-ID sequence)."""
    assert len(vocab) == len(set(vocab)) and all(vocab)
    rows = {}
    for pid, text in sorted(texts.items()):
        assert text
        n = len(text); distance = [None] * n + [(0, 0)]; back = [None] * n
        for start in range(n - 1, -1, -1):
            options = []
            for entry, word in enumerate(vocab):
                end = start + len(word)
                if end <= n and text.startswith(word, start) and distance[end] is not None:
                    f, count = distance[end]
                    options.append((f + word_cost(word), count + 1, entry, end))
            if options:
                f, count, entry, end = min(options)
                distance[start] = (f, count); back[start] = (entry, end)
        if distance[0] is None:
            raise ValueError('dictionary does not cover every source')
        at = 0; sequence = []
        while at < n:
            entry, at = back[at]; sequence.append(entry)
        assert ''.join(vocab[i] for i in sequence) == text
        chars = sum(len(vocab[i]) == 1 for i in sequence)
        assert distance[0] == (10 * chars - len(sequence), len(sequence))
        rows[pid] = {'F': distance[0][0], 'C': chars, 'N': len(sequence), 'sequence': sequence}
    return {'F': sum(r['F'] for r in rows.values()), 'C': sum(r['C'] for r in rows.values()),
            'N': sum(r['N'] for r in rows.values()), 'per_program': rows}


def occurrences(texts, candidates, max_arcs=1_000_000, max_transitions=20_000_000,
                max_pool_characters=2_000_000):
    assert sum(map(len, candidates)) <= max_pool_characters, 'pool character limit'
    trie = {}
    for entry, word in enumerate(candidates):
        node = trie
        for ch in word:
            node = node.setdefault(ch, {})
        assert None not in node
        node[None] = entry
    tails = []; heads = []; entries = []; sources = []; sinks = []; used_positions = []
    base = 0; transitions = 0
    for pid, text in sorted(texts.items()):
        assert text
        sources.append(base); sinks.append(base + len(text))
        for start in range(len(text)):
            node = trie
            for end in range(start, len(text)):
                transitions += 1
                if transitions > max_transitions:
                    raise ValueError('occurrence transition limit')
                node = node.get(text[end])
                if node is None:
                    break
                if None in node:
                    if len(entries) >= max_arcs:
                        raise ValueError('occurrence arc limit')
                    tails.append(base + start); heads.append(base + end + 1); entries.append(node[None])
                    used_positions.append((pid, start))
        base += len(text) + 1
    return tails, heads, entries, sources, sinks, used_positions, base, transitions


def check_point(model, point, objective=None, tolerance=0):
    """All model rows, variable bounds, activations and objective, fail closed."""
    x = np.asarray(point); assert x.shape == (model['variables'],)
    assert np.all(np.isfinite(x))
    assert np.all(x >= -tolerance) and np.all(x <= 1 + tolerance)
    count = model['candidate_count']
    assert np.max(np.abs(x[:count] - np.rint(x[:count])), initial=0) <= tolerance
    values = model['matrix'] @ x
    assert np.all(values >= model['lower'] - tolerance)
    assert np.all(values <= model['upper'] + tolerance)
    value = float(model['cost'] @ x)
    if objective is not None:
        assert abs(value - objective) <= tolerance
    return value


def fingerprint(model):
    """Hash the complete mathematical model and the common incumbent."""
    digest = hashlib.sha256()
    matrix = model['matrix']
    digest.update(str(matrix.shape).encode())
    for a in (matrix.indptr, matrix.indices, matrix.data, model['lower'], model['upper'],
              model['cost'], model['start']):
        digest.update(str(a.dtype).encode()); digest.update(str(a.shape).encode()); digest.update(a.tobytes())
    digest.update(str((model['capacity'], model['candidate_count'], model['initial'])).encode())
    return digest.hexdigest()


def build(texts, candidates, capacity, incumbent, banned=(), **limits):
    started = time.monotonic(); candidates = list(candidates); incumbent = list(incumbent)
    assert type(capacity) is int and capacity >= 0
    assert len(candidates) == len(set(candidates)) and all(candidates)
    assert len(incumbent) == len(set(incumbent)) <= capacity
    assert set(incumbent) <= set(candidates) and not set(candidates) & set(banned)
    C = len(candidates); ids = {s: i for i, s in enumerate(candidates)}
    initial = exact(texts, incumbent)
    path_words = {}
    for pid, row in initial['per_program'].items():
        start = 0
        for entry in row['sequence']:
            word = incumbent[entry]; path_words[(pid, start)] = ids[word]; start += len(word)
        assert start == len(texts[pid])
    tails, heads, entries, sources, sinks, positions, vertices, transitions = occurrences(texts, candidates, **limits)
    tails = np.asarray(tails, dtype=np.int64); heads = np.asarray(heads, dtype=np.int64)
    entries = np.asarray(entries, dtype=np.int64); A = len(entries); V = C + A; arcs = np.arange(A)
    assert np.all(tails < heads)
    flow = coo_matrix((np.concatenate([np.ones(A), -np.ones(A)]),
                       (np.concatenate([tails, heads]), np.concatenate([C + arcs, C + arcs]))), shape=(vertices, V)).tocsr()
    rhs = np.zeros(vertices); rhs[sources] = 1; rhs[sinks] = -1
    links = coo_matrix((np.concatenate([np.ones(A), -np.ones(A)]),
                        (np.concatenate([arcs, arcs]), np.concatenate([C + arcs, entries]))), shape=(A, V)).tocsr()
    budget = coo_matrix((np.ones(C), (np.zeros(C, dtype=int), np.arange(C))), shape=(1, V)).tocsr()
    matrix = vstack([flow, links, budget], format='csc')
    lower = np.concatenate([rhs, np.full(A + 1, -np.inf)])
    upper = np.concatenate([rhs, np.zeros(A), [capacity]])
    cost = np.concatenate([np.zeros(C), np.array([word_cost(candidates[i]) for i in entries])])
    point = np.zeros(V)
    for word in incumbent:
        point[ids[word]] = 1
    for arc, position in enumerate(positions):
        if path_words.get(position) == entries[arc]:
            point[C + arc] = 1
    assert max(matrix.shape) < 2**31 and matrix.nnz < 2**31
    result = {'matrix': matrix, 'lower': lower, 'upper': upper, 'cost': cost, 'start': point,
              'candidate_count': C, 'initial': initial['F'], 'initial_exact': initial,
              'arcs': A, 'variables': V, 'capacity': capacity, 'build_seconds': time.monotonic() - started,
              'transitions': transitions, 'start_nonzero': int(np.count_nonzero(point))}
    check_point(result, point, initial['F'])
    return result


def solve(model, texts, candidates, warm, seconds, banned=(), seed=400):
    # Existing item26 verifies every returned solver row, bound, integrality and
    # objective. It also rejects lost warm incumbents. No frozen code is edited.
    check_point(model, model['start'], model['initial'])
    before = fingerprint(model)
    chosen, receipt = backend.solve(model, candidates, warm, seconds, seed)
    assert fingerprint(model) == before
    receipt['model_sha256'] = before
    replay = None
    if receipt['feasible']:
        assert len(chosen) <= model['capacity'] and not set(chosen) & set(banned)
        replay = exact(texts, chosen)
        assert replay['F'] <= receipt['objective'] + 1e-6
        if receipt['optimal']:
            assert abs(replay['F'] - receipt['objective']) <= 1e-6
        if warm:
            assert replay['F'] <= model['initial']
    return chosen, receipt, replay
