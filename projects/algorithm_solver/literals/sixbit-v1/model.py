"""Exact segmentation models for six-bit (64-code) literal vocabularies.

A program is covered by a vocabulary when it is a concatenation of entries. Entries
that never match a cohort program cannot help, so only substrings are modeled:

- rule W (existing witnessed-literal rules, without the mandatory 96-entry fallback):
  any single character, plus multi-character strings that occur in at least two
  distinct problems, are at most 160 UTF-8 bytes and are not a whole program.
- rule U (unrestricted): any substring that is not a whole cohort program.

Strings that occur at least twice get one binary each ("shared"). Under U a string
that occurs exactly once ("private") can be used only at that occurrence, and every
extension of it at the same start is also private, so private strings become one arc
from each start i to every end j >= first_private_end(i), at cost one entry each.
Nothing here executes candidate source.
"""
from collections import Counter, defaultdict
import numpy as np
from scipy.optimize import milp, linprog, LinearConstraint, Bounds
from scipy.sparse import coo_matrix

MAX_BYTES_W = 160
ESCAPE_ALPHABET = frozenset(chr(10)) | frozenset(chr(i) for i in range(32, 127))


def extents(texts):
    """Per (program, start): longest length occurring at least twice in the corpus
    (rep) and longest length occurring in at least two distinct programs (wit)."""
    rep, wit = {}, {}
    alive = [(p, i) for p in sorted(texts) for i in range(len(texts[p]))]
    for key in alive:
        rep[key] = wit[key] = 0
    length = 1
    while alive:
        counts, docs = Counter(), defaultdict(set)
        live = [(p, i) for p, i in alive if i + length <= len(texts[p])]
        for p, i in live:
            s = texts[p][i:i + length]
            counts[s] += 1
            docs[s].add(p)
        alive = []
        for p, i in live:
            s = texts[p][i:i + length]
            if counts[s] >= 2:
                rep[p, i] = length
                alive.append((p, i))
                if len(docs[s]) >= 2:
                    wit[p, i] = length
        length += 1
    return rep, wit


class Graph:
    """Arcs of every program's segmentation graph under one rule.

    Arc kinds: 'f' shared string (one selection, needs x[string]); 'g' private entry
    (one selection, one entry); 'c' private chain move (free); 'e' escape (codec C)."""

    def __init__(self, texts, rule, escapes=False):
        if rule not in ('W', 'U'):
            raise ValueError('rule must be W or U')
        self.texts, self.rule, self.escapes = texts, rule, escapes
        self.programs = sorted(texts, key=int)
        whole = set(texts.values())
        rep, wit = extents(texts)
        self.strings, index = [], {}
        tails, heads, kinds, strs = [], [], [], []
        self.node_base, self.sinks, nodes = {}, {}, 0
        self.private_starts = {}

        def arc(t, h, k, s=-1):
            tails.append(t); heads.append(h); kinds.append(k); strs.append(s)

        for p in self.programs:
            t, n = texts[p], len(texts[p])
            base = nodes
            self.node_base[p], self.sinks[p] = base, base + n
            nodes += n + 1
            for i in range(n):
                if rule == 'W':
                    top = max(1, min(wit[p, i], MAX_BYTES_W))
                else:
                    top = rep[p, i]
                for j in range(i + 1, i + top + 1):
                    s = t[i:j]
                    if s in whole:
                        continue
                    if s not in index:
                        index[s] = len(self.strings)
                        self.strings.append(s)
                    arc(base + i, base + j, 'f', index[s])
                if escapes and t[i] in ESCAPE_ALPHABET:
                    arc(base + i, base + i + 1, 'e')
            if rule == 'U':
                # Chain a_k (k = 1..n) for starts i >= 1; chain b_k (k < n) for start 0,
                # which may not end at n because a whole program is never an entry.
                starts = {i: i + rep[p, i] + 1 for i in range(n) if i + rep[p, i] + 1 <= n}
                self.private_starts[p] = starts
                a = nodes - 1  # a_k is node a + k
                nodes += n
                for k in range(1, n + 1):
                    arc(a + k, base + k, 'c')
                    if k < n:
                        arc(a + k, a + k + 1, 'c')
                for i, u in starts.items():
                    if i > 0:
                        arc(base + i, a + u, 'g', i)
                if 0 in starts and starts[0] <= n - 1:
                    b = nodes - starts[0]
                    nodes += n - starts[0]
                    for k in range(starts[0], n):
                        arc(b + k, base + k, 'c')
                        if k < n - 1:
                            arc(b + k, b + k + 1, 'c')
                    arc(base + 0, b + starts[0], 'g', 0)
        self.nodes = nodes
        self.tail, self.head = np.array(tails), np.array(heads)
        self.kind, self.string = np.array(kinds), np.array(strs)

    def size(self):
        return {'shared_strings': len(self.strings), 'arcs': int(len(self.kind)),
                'shared_arcs': int((self.kind == 'f').sum()), 'private_entries': int((self.kind == 'g').sum()),
                'escape_arcs': int((self.kind == 'e').sum()), 'nodes': self.nodes}


def build(graph, kind, budget=None, min_covered=None):
    """Variables: x (shared strings), arc flows, then y (programs) for kind 'B'.

    kind 'A': minimize entries, every program covered.
    kind 'B1': maximize covered programs with at most `budget` entries.
    kind 'B2': minimize selections with at least `min_covered` programs and `budget` entries.
    kind 'C': minimize presses (7 per selection, 15 per escape) with `budget` entries."""
    ns, na = len(graph.strings), len(graph.kind)
    ny = len(graph.programs) if kind in ('B1', 'B2') else 0
    nv = ns + na + ny
    cost = np.zeros(nv)
    is_f, is_g, is_e = graph.kind == 'f', graph.kind == 'g', graph.kind == 'e'
    if kind == 'A':
        cost[:ns] = 1
        cost[ns:ns + na][is_g] = 1
    elif kind == 'B1':
        cost[ns + na:] = -1
    elif kind == 'B2':
        cost[ns:ns + na][is_f | is_g] = 1
    elif kind == 'C':
        cost[ns:ns + na][is_f | is_g] = 7
        cost[ns:ns + na][is_e] = 15
    else:
        raise ValueError(kind)
    arcs = np.arange(na)
    rows = [graph.tail, graph.head]
    cols = [ns + arcs, ns + arcs]
    vals = [np.ones(na), -np.ones(na)]
    rhs = np.zeros(graph.nodes)
    for k, p in enumerate(graph.programs):
        source, sink = graph.node_base[p], graph.sinks[p]
        if ny:
            rows += [np.array([source, sink])]
            cols += [np.array([ns + na + k] * 2)]
            vals += [np.array([-1.0, 1.0])]
        else:
            rhs[source], rhs[sink] = 1, -1
    eq = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(graph.nodes, nv)).tocsr()
    f = np.flatnonzero(is_f)
    link = coo_matrix((np.concatenate([np.ones(len(f)), -np.ones(len(f))]),
                       (np.concatenate([np.arange(len(f))] * 2), np.concatenate([ns + f, graph.string[f]]))),
                      shape=(len(f), nv)).tocsr()
    constraints = [LinearConstraint(eq, rhs, rhs), LinearConstraint(link, -np.inf, 0)]
    if budget is not None:
        row = np.zeros(nv)
        row[:ns] = 1
        row[ns:ns + na][is_g] = 1
        constraints.append(LinearConstraint(row[None, :], -np.inf, budget))
    if min_covered is not None:
        row = np.zeros(nv)
        row[ns + na:] = 1
        constraints.append(LinearConstraint(row[None, :], min_covered, np.inf))
    integrality = np.zeros(nv)
    integrality[:ns] = 1
    integrality[ns:ns + na][is_g | is_e] = 1
    integrality[ns + na:] = 1
    return cost, constraints, integrality


def solve_milp(graph, kind, seconds, **extra):
    cost, constraints, integrality = build(graph, kind, **extra)
    res = milp(cost, constraints=constraints, integrality=integrality, bounds=Bounds(0, 1),
               options={'time_limit': float(seconds), 'disp': False})
    return res


def solve_lp(graph, kind, seconds, **extra):
    """LP relaxation; returns the objective, node potentials and the budget multiplier.

    Potentials are the equality-row duals; any values give a valid Lagrangian bound
    (see verify.py), so solver tolerances can only weaken, never invalidate, it."""
    cost, constraints, _ = build(graph, kind, **extra)
    eq, link = constraints[0], constraints[1]
    ub_rows = [link.A]
    ub_rhs = [np.zeros(link.A.shape[0])]
    if extra.get('budget') is not None:
        ub_rows.append(constraints[2].A)
        ub_rhs.append(np.array([extra['budget']], dtype=float))
    from scipy.sparse import vstack
    res = linprog(cost, A_ub=vstack(ub_rows).tocsr(), b_ub=np.concatenate(ub_rhs), A_eq=eq.A, b_eq=eq.lb,
                  bounds=(0, 1), method='highs', options={'time_limit': float(seconds)})
    if res.status != 0:
        return res, None, None
    potentials = res.eqlin.marginals
    mu = float(-res.ineqlin.marginals[-1]) if extra.get('budget') is not None else 0.0
    return res, potentials, mu


def program_potentials(graph, potentials, scale):
    """Integer potentials (value x scale) on program nodes only, as verify.py consumes."""
    return {p: [int(round(float(v) * scale)) for v in potentials[graph.node_base[p]:graph.sinks[p] + 1]]
            for p in graph.programs}


def parse(text, shared, private=(), allowed_private=None, press=None):
    """Exact DP over one program. shared: eligible chosen strings; private starts allowed
    under U map start -> first private end. Returns (cost, private_used, pieces) with
    cost = selections, or presses when press=(selection, escape) is given; ties prefer
    fewer private entries, then fewer escapes, then the shorter first piece."""
    n = len(text)
    best = [None] * (n + 1)
    best[n] = (0, 0, 0, None)
    longest = max(map(len, shared), default=1)
    for i in range(n - 1, -1, -1):
        options = []
        for j in range(i + 1, min(n, i + longest) + 1):
            if text[i:j] in shared and best[j] is not None:
                c = press[0] if press else 1
                options.append((best[j][0] + c, best[j][1], best[j][2], (i, j, 'f')))
        if allowed_private and i in allowed_private:
            for j in range(allowed_private[i], n + 1):
                if best[j] is not None and not (i == 0 and j == n):
                    c = press[0] if press else 1
                    options.append((best[j][0] + c, best[j][1] + 1, best[j][2], (i, j, 'g')))
        if press and text[i] in ESCAPE_ALPHABET and best[i + 1] is not None:
            options.append((best[i + 1][0] + press[1], best[i + 1][1], best[i + 1][2] + 1, (i, i + 1, 'e')))
        if options:
            best[i] = min(options, key=lambda o: (o[0], o[1], o[2], o[3][1]))
    if best[0] is None:
        return None
    pieces, i = [], 0
    while i < n:
        _, _, _, (a, b, k) = best[i]
        pieces.append((text[a:b], k))
        i = b
    return best[0][0], best[0][1], pieces


def solution(graph, res, press=None):
    """Vocabulary and parses from a MILP point: chosen shared strings, private starts
    with a selected entry arc, then an exact per-program DP restricted to them."""
    ns, na = len(graph.strings), len(graph.kind)
    x = res.x
    shared = {graph.strings[k] for k in range(ns) if x[k] > 0.5}
    arcs = x[ns:ns + na]
    starts = defaultdict(dict)
    for a in np.flatnonzero((graph.kind == 'g') & (arcs > 0.5)):
        tail = int(graph.tail[a])
        for p in graph.programs:
            if graph.node_base[p] <= tail <= graph.sinks[p]:
                i = tail - graph.node_base[p]
                starts[p][i] = graph.private_starts[p][i]
                break
    parses = {}
    for p in graph.programs:
        parses[p] = parse(graph.texts[p], shared, allowed_private=starts.get(p), press=press)
    return shared, parses
