"""alphabet96-v2: item 26's direct-HiGHS repair model with per-program nonregression rows, an optional lexicographic N-then-C arc cost and an
optional aggregate fraction row N_ref*C_new <= C_ref*N_new (python-ratiocap-v1; from lexfrac-v1).

build() is seeded-repair-v1/model.build's occurrence-flow model, rebuilt here with arc owners so each fit program p gets
one extra row  sum(arcs of p) <= caps[p]. The supplied incumbent (every incumbent candidate active, its canonical shortest
paths as 0/1 flows) is checked against EVERY row, the cap rows included, before any solve. solve() is item 26's procedure with corrected objective checks (see its docstring).
"""
import importlib.util, time
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, vstack

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
spec = importlib.util.spec_from_file_location('seeded_repair_model', LIT / 'seeded-repair-v1/model.py')
model26 = importlib.util.module_from_spec(spec); spec.loader.exec_module(model26)
analyze = model26.analyze
_h = model26.h  # the HiGHS binding item 26 already imports and pins


def close(a, b):
    """Objective agreement up to a relative 1e-9 (floor 1e-6): float64 noise of ~1e-12 per arc on ~4e5 arcs at costs ~1e5
    gives absolute differences ~1e-2 at objectives ~3e9, which item 26's absolute 1e-6 rejected."""
    return abs(a - b) <= max(1e-6, 1e-9 * max(abs(a), abs(b)))


def solve(model, candidates, warm, seconds, seed=260, integral_arcs=False):
    """item 26's solve() with corrected checks (alphabet96-v2; alphabet96-v1 README).

    item 26 compared the objective with HiGHS's under an ABSOLUTE 1e-6 tolerance, which float64 rounding of a ~4e5-term dot
    product exceeds once the objective reaches ~3e9 (alphabet96-v1's repair abort at M = 131,072). Here the objective and the
    warm-start bound use a relative tolerance of 1e-9. integral_arcs=False keeps item 26's model exactly (activations integer,
    arcs continuous; rows checked on the returned point with item 26's 1e-6, valid for its +-1 flow/link/budget/cap rows);
    integral_arcs=True also declares every arc integer and checks rows exactly on the rounded point (jsratiocap-v1 AMENDMENT-1).
    """
    import numpy as np
    h = _h; started = time.monotonic(); m = model; matrix = m['matrix']; lp = h.HighsLp(); V = m['variables']; R = len(m['upper']); K = m['candidate_count']
    lp.num_col_ = V; lp.num_row_ = R; lp.col_cost_ = m['cost']; lp.col_lower_ = np.zeros(V); lp.col_upper_ = np.ones(V); lp.row_lower_ = m['lower']; lp.row_upper_ = m['upper']
    lp.a_matrix_.num_col_ = V; lp.a_matrix_.num_row_ = R; lp.a_matrix_.format_ = h.MatrixFormat.kColwise
    lp.a_matrix_.start_ = matrix.indptr.astype(np.int32); lp.a_matrix_.index_ = matrix.indices.astype(np.int32); lp.a_matrix_.value_ = matrix.data
    lp.integrality_ = [h.HighsVarType.kInteger] * V if integral_arcs else [h.HighsVarType.kInteger] * K + [h.HighsVarType.kContinuous] * (V - K)
    solver = h._Highs()
    for key, value in {'output_flag': False, 'time_limit': float(seconds), 'mip_rel_gap': 0., 'threads': 1, 'random_seed': seed}.items():
        assert solver.setOptionValue(key, value) == h.HighsStatus.kOk, key
    assert solver.passModel(lp) == h.HighsStatus.kOk
    supplied = None
    if warm:
        point = h.HighsSolution(); point.col_value = m['start']; point.row_value = matrix @ m['start']; point.value_valid = True
        status = solver.setSolution(point); assert status == h.HighsStatus.kOk; supplied = int(status)
    status = solver.run(); assert status != h.HighsStatus.kError
    info = solver.getInfo(); solution = solver.getSolution(); model_status = solver.getModelStatus()
    feasible = bool(solution.value_valid and info.primal_solution_status == h.kSolutionStatusFeasible)
    chosen = []; fun = None; residual = None
    if feasible:
        x = np.asarray(solution.col_value); eps = 1e-6
        assert np.all(x >= -eps) and np.all(x <= 1 + eps)
        ints = x if integral_arcs else x[:K]
        assert np.max(np.abs(ints - np.rint(ints)), initial=0) <= eps  # activations (and, if integral, arcs) integral
        if integral_arcs:
            x = np.rint(x); values = matrix @ x
            assert np.all(values >= m['lower']) and np.all(values <= m['upper'])  # integer data and point: exact
        else:
            values = matrix @ x
            assert np.all(values >= m['lower'] - eps) and np.all(values <= m['upper'] + eps)
        fun = float(m['cost'] @ x); assert close(fun, info.objective_function_value)
        chosen = [s for i, s in enumerate(candidates) if x[i] > .5]
        residual = float(info.max_primal_infeasibility)
    # a supplied valid incumbent must survive a limited solve; no fallback hides a solver failure
    if warm: assert feasible and (fun <= m['initial'] or close(fun, m['initial']))
    def finite(v): return float(v) if np.isfinite(v) else None
    return chosen, {'warm': warm, 'set_solution_status': supplied, 'model_status': int(model_status), 'message': solver.modelStatusToString(model_status),
                    'optimal': model_status == h.HighsModelStatus.kOptimal, 'feasible': feasible, 'objective': fun, 'dual_bound': finite(info.mip_dual_bound),
                    'gap': finite(info.mip_gap), 'nodes': int(info.mip_node_count), 'max_primal_infeasibility': residual,
                    'solver_run_seconds': solver.getRunTime(), 'call_seconds': time.monotonic() - started, 'integral_arcs': integral_arcs}


def build(texts, fixed, candidates, capacity, incumbent, caps, weights=None, char_scale=None, ratio=None):
    # ratio=(N_ref, C_ref): one aggregate row sum_arcs (N_ref*[single] - C_ref) <= 0, i.e. the path fraction C/N stays <= C_ref/N_ref
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
    R = 0 if ratio is None else 1
    if R:
        n_ref, c_ref = ratio
        coef = n_ref * np.asarray(single, dtype=float) - c_ref
        blocks.append(coo_matrix((coef, (np.zeros(A, dtype=int), C + arcs)), shape=(1, V)).tocsr())
    matrix = vstack(blocks, format='csc')
    lower = np.concatenate([rhs, np.full(J + 1 + P + R, -np.inf)])
    upper = np.concatenate([rhs, np.zeros(J), [capacity]] + ([np.array([caps[p] for p in pids], dtype=float)] if P else []) + ([[0.0]] if R else []))
    start = np.zeros(V)
    for word in set(incumbent) - fixed: start[index[word]] = 1
    start[C + np.asarray(used, dtype=int)] = 1
    values = matrix @ start
    assert np.all(start >= 0) and np.all(start <= 1) and np.all(start[:C] == np.floor(start[:C]))
    assert np.all(values >= lower) and np.all(values <= upper) and int(cost @ start) == initial  # every row, caps included
    assert max(matrix.shape) < 2 ** 31 and matrix.nnz < 2 ** 31
    return {'matrix': matrix, 'lower': lower, 'upper': upper, 'cost': cost, 'start': start, 'candidate_count': C, 'initial': initial,
            'arcs': A, 'variables': V, 'cap_rows': P, 'build_seconds': time.monotonic() - started, 'start_nonzero': int(np.count_nonzero(start))}
