"""Item 26's direct-HiGHS repair model with per-program nonregression rows and an optional lexicographic N-then-C arc cost (lexfrac-v1; from tailcap-v1).

build() is seeded-repair-v1/model.build's occurrence-flow model, rebuilt here with arc owners so each fit program p gets
one extra row  sum(arcs of p) <= caps[p]. The supplied incumbent (every incumbent candidate active, its canonical shortest
paths as 0/1 flows) is checked against EVERY row, the cap rows included, before any solve. solve() is item 26's unchanged.
"""
import importlib.util, time
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, vstack

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
spec = importlib.util.spec_from_file_location('seeded_repair_model', LIT / 'seeded-repair-v1/model.py')
model26 = importlib.util.module_from_spec(spec); spec.loader.exec_module(model26)
analyze = model26.analyze
solve = model26.solve


def build(texts, fixed, candidates, capacity, incumbent, caps, weights=None, char_scale=None):
    # char_scale=M: every arc costs M plus 1 if its word is a single character, so the model minimises M*N + C
    assert weights is None or char_scale is None
    started = time.monotonic(); fixed = set(fixed); candidates = list(candidates); C = len(candidates); index = {s: i for i, s in enumerate(candidates)}
    assert len(index) == C and not fixed & set(candidates) and all(fixed | set(candidates))
    assert set(incumbent) <= fixed | set(candidates) and len(set(incumbent) - fixed) <= capacity
    maxlen = max(map(len, fixed | set(candidates)), default=1); tails, heads, entries, owners = [], [], [], []; sources, sinks = [], []
    base = 0; used = []; initial = 0; pids = sorted(texts); single = []
    for q, pid in enumerate(pids):
        text = texts[pid]; seq = analyze.shortest_encode(text, incumbent); starts = {}; offset = 0
        initial += (len(seq) * char_scale + sum(len(incumbent[i]) == 1 for i in seq)) if char_scale else len(seq) * (1 if weights is None else weights[pid])
        assert caps is None or len(seq) <= caps[pid], 'incumbent violates its own cap'
        for idx in seq:
            word = incumbent[idx]; starts[offset] = word; offset += len(word)
        assert offset == len(text)
        sources.append(base); sinks.append(base + len(text))
        for i in range(len(text)):
            for length in range(1, min(maxlen, len(text) - i) + 1):
                word = text[i:i + length]
                if word in fixed or word in index:
                    tails.append(base + i); heads.append(base + i + length); entries.append(-1 if word in fixed else index[word]); owners.append(q); single.append(length == 1)
                    if starts.get(i) == word: used.append(len(entries) - 1)
        base += len(text) + 1
    tails, heads, entries, owners = (np.asarray(x, dtype=np.int64) for x in (tails, heads, entries, owners))
    A = len(entries); V = C + A; arcs = np.arange(A); cost = np.zeros(V)
    if char_scale: cost[C:] = char_scale + np.asarray(single, dtype=float)
    else: cost[C:] = 1 if weights is None else np.array([weights[p] for p in pids], dtype=float)[owners]
    flow = coo_matrix((np.concatenate([np.ones(A), -np.ones(A)]), (np.concatenate([tails, heads]), np.concatenate([C + arcs, C + arcs]))), shape=(base, V)).tocsr()
    rhs = np.zeros(base); rhs[sources] = 1; rhs[sinks] = -1
    optional = np.flatnonzero(entries >= 0); J = len(optional)
    links = coo_matrix((np.concatenate([np.ones(J), -np.ones(J)]), (np.concatenate([np.arange(J), np.arange(J)]), np.concatenate([C + optional, entries[optional]]))), shape=(J, V)).tocsr()
    budget = coo_matrix((np.ones(C), (np.zeros(C, dtype=int), np.arange(C))), shape=(1, V)).tocsr()
    P = 0 if caps is None else len(pids)
    blocks = [flow, links, budget] + ([coo_matrix((np.ones(A), (owners, C + arcs)), shape=(P, V)).tocsr()] if P else [])
    matrix = vstack(blocks, format='csc')
    lower = np.concatenate([rhs, np.full(J + 1 + P, -np.inf)])
    upper = np.concatenate([rhs, np.zeros(J), [capacity]] + ([np.array([caps[p] for p in pids], dtype=float)] if P else []))
    start = np.zeros(V)
    for word in set(incumbent) - fixed: start[index[word]] = 1
    start[C + np.asarray(used, dtype=int)] = 1
    values = matrix @ start
    assert np.all(start >= 0) and np.all(start <= 1) and np.all(start[:C] == np.floor(start[:C]))
    assert np.all(values >= lower) and np.all(values <= upper) and int(cost @ start) == initial  # every row, caps included
    assert max(matrix.shape) < 2 ** 31 and matrix.nnz < 2 ** 31
    return {'matrix': matrix, 'lower': lower, 'upper': upper, 'cost': cost, 'start': start, 'candidate_count': C, 'initial': initial,
            'arcs': A, 'variables': V, 'cap_rows': P, 'build_seconds': time.monotonic() - started, 'start_nonzero': int(np.count_nonzero(start))}
