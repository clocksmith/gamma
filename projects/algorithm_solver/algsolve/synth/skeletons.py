"""Algorithm skeletons: control structure fixed, typed holes filled by a composition.

Each skeleton becomes a stage function `stage_<k>(<inputs>)`. Templates use
placeholder names: `H_<hole>` inside an expression is replaced by the hole's
expression; a statement consisting only of `H_<hole>` is replaced by the
hole's statements. Hole kinds: expr, stmts, choice (from `options`).

`family` separates algorithm-specific skeletons from the generic ones
(formula, scan, simulate). Coverage is reported per family so generic
coverage (close to writing a short program) is not mistaken for coverage by
recognized algorithms.
"""

from __future__ import annotations

SKELETONS: dict[str, dict] = {}


def skeleton(name: str, family: str, doc: str, holes: dict[str, dict], template: str) -> None:
    SKELETONS[name] = {"name": name, "family": family, "doc": doc.strip(), "holes": holes, "template": template.strip("\n")}


E = lambda doc, default=None: {"kind": "expr", "doc": doc, "default": default}  # noqa: E731
S = lambda doc, default=None: {"kind": "stmts", "doc": doc, "default": default}  # noqa: E731
C = lambda doc, options, default=None: {"kind": "choice", "doc": doc, "options": options, "default": default}  # noqa: E731

# --- generic ---------------------------------------------------------------

skeleton("formula", "generic", "Return a single expression over the inputs.",
         {"value": E("the answer")},
         """
    return H_value
""")

skeleton("scan", "generic", "One pass over a sequence with state. Names in step: i, x (index, element).",
         {"seq": E("iterable to scan"), "init": S("initialize state variables", "pass"),
          "step": S("update state for element x at index i"), "result": E("answer from state")},
         """
    H_init
    for i, x in enumerate(H_seq):
        H_step
    return H_result
""")

skeleton("simulate", "generic", "Repeat a step while a condition holds (bounded by max_steps).",
         {"init": S("initialize state", "pass"), "cond": E("continue while true"), "step": S("one step"),
          "result": E("answer"), "max_steps": E("safety bound on iterations", "10**7")},
         """
    H_init
    steps = 0
    while H_cond and steps < H_max_steps:
        H_step
        steps += 1
    return H_result
""")

skeleton("pairs", "generic", "Combine a value over all index pairs i < j. Names: i, j.",
         {"n": E("number of items"), "value": E("value for pair (i, j); None to skip"),
          "combine": C("how to combine pair values", ["sum", "max", "min", "count_true"], "sum"),
          "empty": E("answer when no pair contributes", "0")},
         """
    vals = [H_value for i in range(H_n) for j in range(i + 1, H_n)]
    vals = [v for v in vals if v is not None]
    if not vals:
        return H_empty
    return COMBINE(vals)
""")

# --- arrays and strings -----------------------------------------------------

skeleton("hash_scan", "hash_counting",
         "Scan with a Counter `seen` of earlier keys. Names: i, x, seen, ans. Query before update.",
         {"seq": E("iterable"), "init": S("extra state; seen and ans exist", "pass"),
          "seen_init": S("seed seen before the scan (e.g. seen[0] = 1)", "pass"),
          "query": S("update ans using seen and x/i (and state)"),
          "update": S("record x/i into seen (and state)"), "result": E("answer", "ans")},
         """
    seen = Counter()
    ans = 0
    H_init
    H_seen_init
    for i, x in enumerate(H_seq):
        H_query
        H_update
    return H_result
""")

skeleton("two_pointers", "two_pointers",
         "Indices lo=0, hi=len(arr)-1 moving inward. Names: arr, lo, hi, ans.",
         {"arr": E("sequence (sort it in the expression if needed)"), "init": S("ans and state", "ans = 0"),
          "visit": S("update ans for the pair lo, hi"), "move_lo": E("true to advance lo, else retreat hi"),
          "result": E("answer", "ans")},
         """
    arr = H_arr
    lo, hi = 0, len(arr) - 1
    H_init
    while lo < hi:
        H_visit
        if H_move_lo:
            lo += 1
        else:
            hi -= 1
    return H_result
""")

skeleton("sliding_window", "sliding_window",
         "Variable window [left, right]. Names: seq, left, right, x (= seq[right]), y (= seq[left] on removal).",
         {"seq": E("sequence"), "init": S("window state and ans", "ans = 0"), "add": S("add x to window"),
          "invalid": E("true while the window must shrink"), "remove": S("remove y from window"),
          "update": S("update ans for the valid window"), "result": E("answer", "ans")},
         """
    seq = H_seq
    left = 0
    H_init
    for right, x in enumerate(seq):
        H_add
        while left <= right and H_invalid:
            y = seq[left]
            H_remove
            left += 1
        H_update
    return H_result
""")

skeleton("binary_search_answer", "binary_search",
         "Search a monotone predicate over integers [lo, hi]. Name in feasible: x.",
         {"lo": E("lowest candidate"), "hi": E("highest candidate"), "feasible": E("monotone predicate of x"),
          "mode": C("first x where feasible becomes true, or last x where it is still true", ["first_true", "last_true"]),
          "result": E("answer from found value `found`", "found")},
         """
    found = (c_first_true if 'H_mode' == 'first_true' else c_last_true)(H_lo, H_hi, lambda x: H_feasible)
    return H_result
""")

skeleton("monotonic_stack", "monotonic_stack",
         "Next/previous index under a comparison via c_next_index/c_prev_index. Names: nxt, prv, seq.",
         {"seq": E("sequence"), "better_next": E("lambda a, b: ... for next index", "lambda a, b: a > b"),
          "better_prev": E("lambda a, b: ... for previous index", "lambda a, b: a > b"),
          "result": E("answer from nxt, prv, seq")},
         """
    seq = H_seq
    nxt = c_next_index(seq, H_better_next)
    prv = c_prev_index(seq, H_better_prev)
    return H_result
""")

skeleton("heap_process", "heap",
         "Process a heap until empty or stop. Names: heap, item (popped), ans.",
         {"init": S("build heap (list) and ans; heapify happens after", "ans = 0"), "stop": E("stop when true", "False"),
          "process": S("handle popped item; may heappush(heap, ...)"), "result": E("answer", "ans"),
          "max_steps": E("safety bound", "10**7")},
         """
    heap = []
    H_init
    heapify(heap)
    steps = 0
    while heap and not H_stop and steps < H_max_steps:
        item = heappop(heap)
        H_process
        steps += 1
    return H_result
""")

skeleton("sort_scan", "greedy_sorting",
         "Sort items by a key, then scan. Names: i, x, items.",
         {"items": E("items to sort"), "key": E("lambda x: sort key", "lambda x: x"),
          "reverse": C("descending order", ["False", "True"], "False"),
          "init": S("state", "ans = 0"), "step": S("greedy update for x"), "result": E("answer", "ans")},
         """
    items = sorted(H_items, key=H_key, reverse=H_reverse)
    H_init
    for i, x in enumerate(items):
        H_step
    return H_result
""")

# --- graphs -----------------------------------------------------------------

skeleton("graph_bfs", "graph_traversal",
         "Unweighted shortest distances. Names: adj, dist.",
         {"n": E("node count"), "edges": E("iterable of (u, v)"), "directed": C("directed edges", ["False", "True"], "False"),
          "sources": E("iterable of start nodes"), "result": E("answer from dist (-1 = unreachable)")},
         """
    adj = c_adjacency(H_n, H_edges, directed=H_directed)
    dist = c_bfs(H_n, adj, H_sources)
    return H_result
""")

skeleton("grid_bfs", "graph_traversal",
         "4-neighbour BFS on a grid. Names: grid, dist (dict of reached cells), rows, cols.",
         {"grid": E("2D grid"), "passable": E("lambda v: cell value passable"), "sources": E("iterable of (r, c)"),
          "result": E("answer from dist")},
         """
    grid = H_grid
    rows, cols = len(grid), len(grid[0]) if grid else 0
    dist = c_grid_bfs(grid, H_sources, H_passable)
    return H_result
""")

skeleton("dijkstra", "shortest_path",
         "Non-negative weighted shortest distances. Names: adj, dist.",
         {"n": E("node count"), "edges": E("iterable of (u, v, w)"), "directed": C("directed", ["False", "True"], "False"),
          "sources": E("iterable of start nodes"), "result": E("answer from dist (inf = unreachable)")},
         """
    adj = c_adjacency(H_n, H_edges, directed=H_directed, weighted=True)
    dist = c_dijkstra(H_n, adj, H_sources)
    return H_result
""")

skeleton("components", "union_find",
         "Union pairs, then answer from the partition. Names: dsu.",
         {"n": E("element count"), "pairs": E("iterable of (a, b) to union"), "result": E("answer from dsu")},
         """
    dsu = c_DSU(H_n)
    for a, b in H_pairs:
        dsu.union(a, b)
    return H_result
""")

skeleton("mst", "union_find", "Minimum spanning forest. Names: total, chosen, parts.",
         {"n": E("node count"), "edges": E("iterable of (u, v, w)"), "result": E("answer", "total")},
         """
    total, chosen, parts = c_kruskal(H_n, list(H_edges))
    return H_result
""")

skeleton("topo_order", "graph_traversal", "Topological order (None if cyclic). Names: adj, order.",
         {"n": E("node count"), "edges": E("iterable of (u, v): u before v"), "result": E("answer from order")},
         """
    adj = c_adjacency(H_n, H_edges, directed=True)
    order = c_topo(H_n, adj)
    return H_result
""")

# --- dynamic programming ----------------------------------------------------

skeleton("dp_1d", "dynamic_programming",
         "dp[i] for i in [start, size) from earlier entries. Names: dp, i.",
         {"size": E("table size"), "fill": E("initial value of every entry", "0"), "base": S("set base entries", "pass"),
          "start": E("first computed index", "1"), "transition": E("value of dp[i]"), "result": E("answer", "dp[-1]")},
         """
    dp = [H_fill] * (H_size)
    H_base
    for i in range(H_start, H_size):
        dp[i] = H_transition
    return H_result
""")

skeleton("dp_2d", "dynamic_programming",
         "dp[i][j] over a rows x cols table in row-major order. Names: dp, i, j.",
         {"rows": E("rows"), "cols": E("cols"), "fill": E("initial value", "0"), "base": S("set base entries", "pass"),
          "row_start": E("first computed row", "1"), "col_start": E("first computed column", "1"),
          "transition": E("value of dp[i][j]"), "result": E("answer", "dp[-1][-1]")},
         """
    dp = [[H_fill] * (H_cols) for _ in range(H_rows)]
    H_base
    for i in range(H_row_start, H_rows):
        for j in range(H_col_start, H_cols):
            dp[i][j] = H_transition
    return H_result
""")

skeleton("memo", "dynamic_programming",
         "Memoized recursion f(*state). Names: f, and the state parameter names in `params`.",
         {"params": E("tuple of state parameter names as strings, e.g. ('i', 'k')"),
          "base_cond": E("true when the state is terminal"), "base_value": E("value at a terminal state"),
          "transition": E("value of f(state) from smaller states"), "start": E("tuple of initial state values"),
          "mod": E("modulus applied to results, or None", "None")},
         """
    @cache
    def f(*state):
        H_bind_params
        if H_base_cond:
            return H_base_value
        value = H_transition
        return value % H_mod if H_mod is not None else value
    return f(*H_start)
""")

skeleton("subset_enum", "backtracking",
         "Enumerate bitmasks over n items. Names: mask.",
         {"n": E("number of items (small)"), "valid": E("mask is acceptable", "True"), "value": E("value for mask"),
          "combine": C("combine values of valid masks", ["max", "min", "sum", "count"], "max"),
          "empty": E("answer when no mask is valid", "0")},
         """
    vals = [H_value for mask in range(1 << H_n) if H_valid]
    if not vals:
        return H_empty
    return COMBINE(vals)
""")

COMBINE_EXPR = {"sum": "sum(vals)", "max": "max(vals)", "min": "min(vals)", "count_true": "sum(1 for v in vals if v)",
                "count": "len(vals)"}

# Components each skeleton relies on.
SKELETON_COMPONENTS = {
    "binary_search_answer": ["binsearch"], "monotonic_stack": ["monostack"], "graph_bfs": ["graph"],
    "grid_bfs": ["grid"], "dijkstra": ["graph"], "components": ["dsu"], "mst": ["kruskal"], "topo_order": ["graph"],
}


def catalog_text() -> str:
    parts = []
    for spec in SKELETONS.values():
        holes = "\n".join(
            f"    {name} ({h['kind']}{'; options ' + '/'.join(h['options']) if h['kind'] == 'choice' else ''}"
            f"{'; default ' + repr(h['default']) if h.get('default') is not None else ''}): {h['doc']}"
            for name, h in spec["holes"].items()
        )
        parts.append(f"[{spec['name']}] family={spec['family']}\n  {spec['doc']}\n  holes:\n{holes}")
    return "\n\n".join(parts)
