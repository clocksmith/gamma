"""Contract tests for algorithm_solver synthesis components, grammar and renderer.

Components are checked against brute-force references on random inputs.
These are tested contracts, not formal verification.
"""

from __future__ import annotations

import itertools
from pathlib import Path
import random
import sys

import pytest

_LANE = Path(__file__).resolve().parents[1] / "projects" / "algorithm_solver"
if str(_LANE) not in sys.path:
    sys.path.insert(0, str(_LANE))

from algsolve.synth import components, grammar, render  # noqa: E402

RNG = random.Random(20261017)


def load(*names: str) -> dict:
    ns: dict = {}
    exec(render.PREAMBLE, ns)
    for name in components.resolve(list(names)):
        exec(components.COMPONENTS[name]["source"], ns)
    return ns


def test_dsu_matches_brute_force_connectivity():
    ns = load("dsu")
    for _ in range(50):
        n = RNG.randint(1, 12)
        pairs = [(RNG.randrange(n), RNG.randrange(n)) for _ in range(RNG.randint(0, 15))]
        dsu = ns["c_DSU"](n)
        for a, b in pairs:
            dsu.union(a, b)
        # brute force: transitive closure
        reach = {i: {i} for i in range(n)}
        changed = True
        while changed:
            changed = False
            for a, b in pairs:
                merged = reach[a] | reach[b]
                for x in merged:
                    if reach[x] != merged:
                        reach[x] = set(merged)
                        changed = True
        assert dsu.count == len({frozenset(s) for s in reach.values()})
        for i in range(n):
            assert dsu.size(i) == len(reach[i])
            for j in range(n):
                assert (dsu.find(i) == dsu.find(j)) == (j in reach[i])


def test_fenwick_and_segtree_match_brute_force():
    ns = load("fenwick", "segtree")
    for _ in range(30):
        n = RNG.randint(1, 20)
        vals = [RNG.randint(-9, 9) for _ in range(n)]
        fw = ns["c_Fenwick"](n)
        for i, v in enumerate(vals):
            fw.add(i, v)
        st = ns["c_SegTree"](vals, min, float("inf"))
        for _ in range(20):
            i, v = RNG.randrange(n), RNG.randint(-9, 9)
            fw.add(i, v - vals[i])
            vals[i] = v
            st.update(i, v)
            l, r = sorted((RNG.randint(0, n), RNG.randint(0, n)))
            assert fw.range(l, r) == sum(vals[l:r])
            assert st.query(l, r) == (min(vals[l:r]) if r > l else float("inf"))


def test_number_theory_components():
    ns = load("sieve", "modcomb")
    is_prime = ns["c_sieve"](200)
    for k in range(201):
        assert is_prime[k] == (k > 1 and all(k % d for d in range(2, int(k ** 0.5) + 1)))
    mc = ns["c_ModComb"](60, 10**9 + 7)
    import math
    for a in range(61):
        for b in range(-1, a + 2):
            assert mc.ncr(a, b) == (math.comb(a, b) % (10**9 + 7) if 0 <= b <= a else 0)


def test_lis_matches_brute_force():
    ns = load("lis")
    for _ in range(100):
        seq = [RNG.randint(0, 6) for _ in range(RNG.randint(0, 9))]
        best_strict = best_weak = 0
        for mask in range(1 << len(seq)):
            sub = [seq[i] for i in range(len(seq)) if mask >> i & 1]
            if all(a < b for a, b in zip(sub, sub[1:])):
                best_strict = max(best_strict, len(sub))
            if all(a <= b for a, b in zip(sub, sub[1:])):
                best_weak = max(best_weak, len(sub))
        assert ns["c_lis_length"](seq) == best_strict
        assert ns["c_lis_length"](seq, strict=False) == best_weak


def test_string_components():
    ns = load("kmp", "zfunc")
    for _ in range(100):
        text = "".join(RNG.choice("ab") for _ in range(RNG.randint(0, 15)))
        pattern = "".join(RNG.choice("ab") for _ in range(RNG.randint(1, 3)))
        expected = [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]
        assert ns["c_find_all"](text, pattern) == expected
        z = ns["c_z_function"](text)
        for i in range(len(text)):
            k = 0
            while i + k < len(text) and text[k] == text[i + k]:
                k += 1
            assert z[i] == k


def test_graph_components():
    ns = load("graph", "kruskal")
    for _ in range(30):
        n = RNG.randint(1, 8)
        edges = [(RNG.randrange(n), RNG.randrange(n), RNG.randint(0, 9)) for _ in range(RNG.randint(0, 8))]
        adj = ns["c_adjacency"](n, edges, directed=True, weighted=True)
        dist = ns["c_dijkstra"](n, adj, [0])
        # Bellman-Ford reference
        ref = [float("inf")] * n
        ref[0] = 0
        for _ in range(n):
            for u, v, w in edges:
                ref[v] = min(ref[v], ref[u] + w)
        assert dist == ref
        unweighted = ns["c_adjacency"](n, [(u, v) for u, v, _ in edges], directed=False)
        bfs = ns["c_bfs"](n, unweighted, [0])
        assert all((bfs[v] == -1) == (ref_reach == float("inf")) for v, ref_reach in enumerate(
            _undirected_reach(n, edges)))
        total, chosen, parts = ns["c_kruskal"](n, edges)
        assert total == _brute_mst(n, edges)
        dag = [(u, v) for u, v, _ in edges if u < v]
        order = ns["c_topo"](n, ns["c_adjacency"](n, dag, directed=True))
        position = {v: k for k, v in enumerate(order)}
        assert all(position[u] < position[v] for u, v in dag)
    cyclic = ns["c_adjacency"](2, [(0, 1), (1, 0)], directed=True)
    assert ns["c_topo"](2, cyclic) is None


def _undirected_reach(n, edges):
    reach = [float("inf")] * n
    reach[0] = 0
    for _ in range(n):
        for u, v, _w in edges:
            if reach[u] == 0 or reach[v] == 0:
                reach[u] = reach[v] = 0
    return reach


def _brute_mst(n, edges):
    best = None
    target_parts = None
    for k in range(len(edges) + 1):
        for subset in itertools.combinations(edges, k):
            parent = list(range(n))

            def find(x):
                while parent[x] != x:
                    x = parent[x]
                return x

            ok = True
            for u, v, _w in subset:
                ru, rv = find(u), find(v)
                if ru == rv:
                    ok = False
                    break
                parent[ru] = rv
            if not ok:
                continue
            parts = len({find(i) for i in range(n)})
            weight = sum(w for _u, _v, w in subset)
            if target_parts is None or parts < target_parts or (parts == target_parts and weight < best):
                target_parts, best = parts, weight
    return best


def test_binary_search_and_monostack_and_prefix():
    ns = load("binsearch", "monostack", "prefix", "intervals", "trie", "grid")
    for _ in range(100):
        lo, hi = sorted((RNG.randint(-20, 20), RNG.randint(-20, 20)))
        t = RNG.randint(-25, 25)
        assert ns["c_first_true"](lo, hi, lambda x: x >= t) == next((x for x in range(lo, hi + 1) if x >= t), hi + 1)
        assert ns["c_last_true"](lo, hi, lambda x: x <= t) == next((x for x in range(hi, lo - 1, -1) if x <= t), lo - 1)
        seq = [RNG.randint(0, 5) for _ in range(RNG.randint(0, 10))]
        nxt = ns["c_next_index"](seq, lambda a, b: a > b)
        prv = ns["c_prev_index"](seq, lambda a, b: a >= b)
        for i, x in enumerate(seq):
            assert nxt[i] == next((j for j in range(i + 1, len(seq)) if seq[j] > x), len(seq))
            assert prv[i] == next((j for j in range(i - 1, -1, -1) if seq[j] >= x), -1)
        assert ns["c_prefix_sums"](seq) == [sum(seq[:i]) for i in range(len(seq) + 1)]
    intervals = [[1, 3], [2, 6], [8, 10], [10, 12]]
    assert ns["c_merge_intervals"](intervals) == [[1, 6], [8, 12]]
    trie = ns["c_Trie"]()
    for w in ("apple", "app", "bat"):
        trie.insert(w)
    assert trie.count_prefix("ap") == 2 and trie.contains("app") and not trie.contains("ap")
    grid = [[0, 0, 1], [1, 0, 1], [0, 0, 0]]
    dist = ns["c_grid_bfs"](grid, [(0, 0)], lambda v: v == 0)
    assert dist[(2, 0)] == 4 and (0, 2) not in dist
    P = ns["c_prefix_2d"](grid)
    assert ns["c_rect_sum"](P, 0, 1, 2, 3) == 2  # rows 0-1, cols 1-2


def test_grammar_rejects_free_form_code():
    for bad in ("__import__('os')", "open('x').read()", "(lambda: exec('1'))()", "x.__class__"):
        with pytest.raises(grammar.GrammarError):
            grammar.check_expr(bad)
    for bad in ("def f():\n    pass", "import os", "while True:\n    pass", "for a in x:\n    for b in y:\n        pass",
                "x = 1\n" * 7):
        with pytest.raises(grammar.GrammarError):
            grammar.check_stmts(bad)
    assert grammar.check_expr("max(dp[i - 1], dp[i - 2] + nums[i])").nodes > 0


def test_render_functional_and_stdin_compositions():
    two_sum = {
        "stages": [{"skeleton": "hash_scan", "inputs": ["nums", "target"], "output": "res", "holes": {
            "seq": "nums", "init": "pos = {}; ans = None",
            "query": "ans = [pos[target - x], i] if ans is None and target - x in pos else ans",
            "update": "pos[x] = i if x not in pos else pos[x]", "result": "ans"}}],
        "answer": "res",
    }
    rendered = render.render(two_sum, method="twoSum", params=["nums", "target"])
    ns: dict = {}
    exec(rendered.source, ns)
    assert ns["Solution"]().twoSum([2, 7, 11, 15], 9) == [0, 1]
    assert rendered.families == ["hash_counting"]

    robber = {"stages": [{"skeleton": "memo", "inputs": ["nums"], "output": "best", "holes": {
        "params": "('i',)", "base_cond": "i >= len(nums)", "base_value": "0",
        "transition": "max(f(i + 1), nums[i] + f(i + 2))", "start": "(0,)"}}], "answer": "best"}
    ns = {}
    exec(render.render(robber, method="rob", params=["nums"]).source, ns)
    assert ns["Solution"]().rob([2, 7, 9, 3, 1]) == 12

    stdin_sum = {"io": {"mode": "stdin", "cases": "multi", "parse": "a, b = ni(), ni()", "output": "s"},
                 "stages": [{"skeleton": "formula", "inputs": ["a", "b"], "output": "s", "holes": {"value": "a + b"}}]}
    source = render.render(stdin_sum).source
    import io, contextlib
    out = io.StringIO()
    old = sys.stdin
    sys.stdin = io.StringIO("2\n1 2\n5 7\n")
    try:
        with contextlib.redirect_stdout(out):
            exec(source, {"__name__": "x"})
    finally:
        sys.stdin = old
    assert out.getvalue().split() == ["3", "12"]


def test_render_rejects_out_of_grammar_holes():
    bad = {"stages": [{"skeleton": "formula", "inputs": ["x"], "output": "y",
                       "holes": {"value": "__import__('os').system('true')"}}], "answer": "y"}
    with pytest.raises(grammar.GrammarError):
        render.render(bad, method="f", params=["x"])
    with pytest.raises(grammar.GrammarError):
        render.render({"stages": [{"skeleton": "nope", "inputs": [], "holes": {}}], "answer": "1"}, method="f", params=[])


def test_structure_conversions_round_trip():
    ns = load("structures")
    exec("class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val, self.next = val, next\n"
         "class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n"
         "        self.val, self.left, self.right = val, left, right\n", ns)
    for values in ([], [1], [3, 1, 2, 2]):
        assert ns["c_list_values"](ns["c_list_from"](values)) == values
    for values in ([], [1], [4, 2, 7, 1, 3, None, 9], [1, None, 2, None, 3]):
        assert ns["c_tree_values"](ns["c_tree_from"](values)) == values
    assert grammar.check_expr("set(a).union(b)").nodes > 0


def test_referenced_components_are_included_automatically():
    composition = {"stages": [{"skeleton": "formula", "inputs": ["nums"], "output": "n",
                               "holes": {"value": "c_lis_length(nums)"}}], "answer": "n"}
    rendered = render.render(composition, method="lengthOfLIS", params=["nums"])
    assert "lis" in rendered.components
    ns: dict = {}
    exec(rendered.source, ns)
    assert ns["Solution"]().lengthOfLIS([10, 9, 2, 5, 3, 7, 101, 18]) == 4
