"""Development problem families for Section 4 of the BITS paired-switch experiment.

Covers three distinct algorithmic families:
  1. duplicate_handling   (helper: skip_equal(xs, i))
  2. interval_processing  (helper: merge_span(acc, start, end))
  3. graph_traversal      (helper: push_unvisited(queue, visited, neighbors))

Each family includes three verified problems spanning all three helper utility regimes:
  - useful_once         (helper fixes a single call site cleanly)
  - repeatedly_useful   (helper is reused across multiple passes/call sites)
  - irrelevant_decoy    (helper looks superficially applicable by keywords/types,
                         but the actual two-attempt failure has a different cause)

`dup_02_unique_triplets_zero` is the canonical Section 1 `skip_equal(xs, i)` fixture.
"""

from __future__ import annotations

from typing import Any

from helpers import HELPER_SPECS
from verifier import HELPER_TOKEN_SYMBOL, SingleBindRegistry, verify_candidate


DEV_PROBLEMS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Family 1: duplicate_handling (helper: skip_equal)
    # ------------------------------------------------------------------
    {
        "problem_id": "dup_01_dedup_sorted_runs",
        "family": "duplicate_handling",
        "utility_regime": "useful_once",
        "helper_name": "skip_equal",
        "entry_point": "unique_sorted_values",
        "statement": (
            "Write `unique_sorted_values(xs)` taking a sorted list of integers `xs` and returning "
            "a list containing each distinct value once in ascending order, without using set()."
        ),
        "failed_attempts": [
            (
                "def unique_sorted_values(xs):\n"
                "    out = []\n"
                "    i = 0\n"
                "    while i < len(xs):\n"
                "        out.append(xs[i])\n"
                "        if i + 1 < len(xs) and xs[i] == xs[i + 1]:\n"
                "            i += 2\n"
                "        else:\n"
                "            i += 1\n"
                "    return out\n"
            ),
            (
                "def unique_sorted_values(xs):\n"
                "    out = []\n"
                "    for i in range(len(xs)):\n"
                "        if xs[i] != xs[i + 1]:\n"
                "            out.append(xs[i])\n"
                "    return out\n"
            ),
        ],
        "reference_with_helper": (
            "def unique_sorted_values(xs):\n"
            "    out = []\n"
            "    i = 0\n"
            "    while i < len(xs):\n"
            "        out.append(xs[i])\n"
            "        i = {OP}(xs, i)\n"
            "    return out\n"
        ),
        "public_cases": [
            {"label": "empty_list", "args": [[]], "expected": []},
            {"label": "run_of_duplicates", "args": [[1, 2, 2, 2, 5]], "expected": [1, 2, 5]},
            {"label": "end_of_array_duplicates", "args": [[1, 3, 3]], "expected": [1, 3]},
        ],
        "hidden_cases": [
            {"label": "all_equal", "args": [[4, 4, 4, 4]], "expected": [4]},
            {"label": "singleton", "args": [[9]], "expected": [9]},
            {"label": "negatives_and_runs", "args": [[-5, -5, -1, 0, 0, 0, 7, 7]], "expected": [-5, -1, 0, 7]},
        ],
    },
    {
        "problem_id": "dup_02_unique_triplets_zero",
        "family": "duplicate_handling",
        "utility_regime": "repeatedly_useful",
        "canonical_section1_fixture": True,
        "helper_name": "skip_equal",
        "entry_point": "unique_zero_triplets",
        "statement": (
            "Write `unique_zero_triplets(nums)` taking a list of integers `nums` and returning "
            "all unique triplets `[a, b, c]` with `a <= b <= c` and `a + b + c == 0`, "
            "ordered lexicographically. Do not emit duplicate triplets when input contains duplicate values."
        ),
        "failed_attempts": [
            (
                "def unique_zero_triplets(nums):\n"
                "    xs = sorted(nums)\n"
                "    res = []\n"
                "    n = len(xs)\n"
                "    for i in range(n - 2):\n"
                "        lo, hi = i + 1, n - 1\n"
                "        while lo < hi:\n"
                "            s = xs[i] + xs[lo] + xs[hi]\n"
                "            if s == 0:\n"
                "                res.append([xs[i], xs[lo], xs[hi]])\n"
                "                lo += 1\n"
                "                hi -= 1\n"
                "            elif s < 0:\n"
                "                lo += 1\n"
                "            else:\n"
                "                hi -= 1\n"
                "    return res\n"
            ),
            (
                "def unique_zero_triplets(nums):\n"
                "    xs = sorted(nums)\n"
                "    res = []\n"
                "    n = len(xs)\n"
                "    i = 0\n"
                "    while i < n - 2:\n"
                "        lo, hi = i + 1, n - 1\n"
                "        while lo < hi:\n"
                "            s = xs[i] + xs[lo] + xs[hi]\n"
                "            if s == 0:\n"
                "                res.append([xs[i], xs[lo], xs[hi]])\n"
                "                if xs[lo] == xs[lo + 1]:\n"
                "                    lo += 2\n"
                "                else:\n"
                "                    lo += 1\n"
                "                hi -= 1\n"
                "            elif s < 0:\n"
                "                lo += 1\n"
                "            else:\n"
                "                hi -= 1\n"
                "        if xs[i] == xs[i + 1]:\n"
                "            i += 2\n"
                "        else:\n"
                "            i += 1\n"
                "    return res\n"
            ),
        ],
        "reference_with_helper": (
            "def unique_zero_triplets(nums):\n"
            "    xs = sorted(nums)\n"
            "    res = []\n"
            "    n = len(xs)\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        lo = i + 1\n"
            "        hi = n - 1\n"
            "        while lo < hi:\n"
            "            s = xs[i] + xs[lo] + xs[hi]\n"
            "            if s == 0:\n"
            "                res.append([xs[i], xs[lo], xs[hi]])\n"
            "                lo = {OP}(xs, lo)\n"
            "                val_hi = xs[hi]\n"
            "                while hi > lo and xs[hi] == val_hi:\n"
            "                    hi -= 1\n"
            "            elif s < 0:\n"
            "                lo = {OP}(xs, lo)\n"
            "            else:\n"
            "                hi -= 1\n"
            "        i = {OP}(xs, i)\n"
            "    return res\n"
        ),
        "public_cases": [
            {
                "label": "empty_suffix_short_list",
                "args": [[0, 0]],
                "expected": [],
            },
            {
                "label": "run_of_duplicates",
                "args": [[-1, 0, 1, 2, -1, -4]],
                "expected": [[-1, -1, 2], [-1, 0, 1]],
            },
            {
                "label": "triple_duplicate_run_end_of_array",
                "args": [[-2, -2, -2, 0, 0, 0, 2, 2, 2]],
                "expected": [[-2, 0, 2], [0, 0, 0]],
            },
        ],
        "hidden_cases": [
            {"label": "all_zeros", "args": [[0, 0, 0, 0, 0]], "expected": [[0, 0, 0]]},
            {"label": "no_solution_duplicates", "args": [[1, 1, 1, 2, 2, 2]], "expected": []},
            {
                "label": "multi_runs",
                "args": [[-3, -3, -1, -1, 0, 1, 2, 2, 4, 4]],
                "expected": [[-3, -1, 4], [-3, 1, 2], [-1, -1, 2], [-1, 0, 1]],
            },
        ],
    },
    {
        "problem_id": "dup_03_max_gap_unsorted_decoy",
        "family": "duplicate_handling",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "skip_equal",
        "entry_point": "max_sorted_gap",
        "statement": (
            "Write `max_sorted_gap(nums)` returning the maximum difference between successive "
            "elements of `nums` in sorted order (0 if fewer than 2 elements). Input may include "
            "negative numbers and duplicate values."
        ),
        "failed_attempts": [
            (
                "def max_sorted_gap(nums):\n"
                "    if len(nums) < 2:\n"
                "        return 0\n"
                "    best = 0\n"
                "    for i in range(len(nums) - 1):\n"
                "        diff = nums[i + 1] - nums[i]\n"
                "        if diff > best:\n"
                "            best = diff\n"
                "    return best\n"
            ),
            (
                "def max_sorted_gap(nums):\n"
                "    if len(nums) < 2:\n"
                "        return 0\n"
                "    xs = sorted(nums)\n"
                "    return xs[-1] - xs[0]\n"
            ),
        ],
        "reference_with_helper": (
            "def max_sorted_gap(nums):\n"
            "    if len(nums) < 2:\n"
            "        return 0\n"
            "    xs = sorted(nums)\n"
            "    return max(xs[i + 1] - xs[i] for i in range(len(xs) - 1))\n"
        ),
        "public_cases": [
            {"label": "unsorted_order_bug", "args": [[3, 6, 9, 1]], "expected": 3},
            {"label": "span_not_adjacent", "args": [[10, 1, 4, 20]], "expected": 10},
            {"label": "negative_values", "args": [[-10, -2, -7]], "expected": 5},
        ],
        "hidden_cases": [
            {"label": "singleton", "args": [[5]], "expected": 0},
            {"label": "with_duplicates", "args": [[4, 4, 1, 1, 9]], "expected": 5},
            {"label": "all_equal", "args": [[7, 7, 7]], "expected": 0},
        ],
    },
    # ------------------------------------------------------------------
    # Family 2: interval_processing (helper: merge_span)
    # ------------------------------------------------------------------
    {
        "problem_id": "int_01_merge_overlapping",
        "family": "interval_processing",
        "utility_regime": "useful_once",
        "helper_name": "merge_span",
        "entry_point": "merge_intervals",
        "statement": (
            "Write `merge_intervals(intervals)` taking a list of closed intervals `[start, end]` "
            "and returning a sorted list of non-overlapping intervals covering the same union."
        ),
        "failed_attempts": [
            (
                "def merge_intervals(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    xs = sorted(intervals)\n"
                "    out = [xs[0]]\n"
                "    for s, e in xs[1:]:\n"
                "        if s < out[-1][1]:\n"
                "            out[-1][1] = e\n"
                "        else:\n"
                "            out.append([s, e])\n"
                "    return out\n"
            ),
            (
                "def merge_intervals(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    xs = sorted(intervals)\n"
                "    out = [xs[0]]\n"
                "    for s, e in xs[1:]:\n"
                "        if s <= out[-1][1]:\n"
                "            out[-1][1] = e\n"
                "        else:\n"
                "            out.append([s, e])\n"
                "    return out\n"
            ),
        ],
        "reference_with_helper": (
            "def merge_intervals(intervals):\n"
            "    acc = []\n"
            "    for start, end in sorted(intervals):\n"
            "        acc = {OP}(acc, start, end)\n"
            "    return acc\n"
        ),
        "public_cases": [
            {"label": "touching_endpoints", "args": [[[1, 3], [3, 5]]], "expected": [[1, 5]]},
            {"label": "contained_interval_shrink_bug", "args": [[[1, 10], [2, 5]]], "expected": [[1, 10]]},
            {"label": "empty_input", "args": [[]], "expected": []},
        ],
        "hidden_cases": [
            {"label": "unsorted_multi", "args": [[[8, 10], [1, 3], [2, 6], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]]},
            {"label": "nested_chain", "args": [[[1, 20], [2, 3], [4, 15], [16, 19]]], "expected": [[1, 20]]},
        ],
    },
    {
        "problem_id": "int_02_union_and_insert",
        "family": "interval_processing",
        "utility_regime": "repeatedly_useful",
        "helper_name": "merge_span",
        "entry_point": "insert_and_union",
        "statement": (
            "Write `insert_and_union(base, extra)` taking two unsorted lists of closed intervals, "
            "normalizing each and returning the merged disjoint union of all intervals."
        ),
        "failed_attempts": [
            (
                "def insert_and_union(base, extra):\n"
                "    out = sorted(base)\n"
                "    for s, e in sorted(extra):\n"
                "        if out and s < out[-1][1]:\n"
                "            out[-1][1] = e\n"
                "        else:\n"
                "            out.append([s, e])\n"
                "    return out\n"
            ),
            (
                "def insert_and_union(base, extra):\n"
                "    merged = []\n"
                "    for s, e in sorted(base + extra):\n"
                "        if merged and s <= merged[-1][1]:\n"
                "            merged[-1][1] = e\n"
                "        else:\n"
                "            merged.append([s, e])\n"
                "    return merged\n"
            ),
        ],
        "reference_with_helper": (
            "def insert_and_union(base, extra):\n"
            "    first = []\n"
            "    for start, end in sorted(base):\n"
            "        first = {OP}(first, start, end)\n"
            "    acc = []\n"
            "    for start, end in sorted(first + list(extra)):\n"
            "        acc = {OP}(acc, start, end)\n"
            "    return acc\n"
        ),
        "public_cases": [
            {
                "label": "contained_and_touching",
                "args": [[[1, 8], [10, 12]], [[2, 4], [8, 10]]],
                "expected": [[1, 12]],
            },
            {
                "label": "empty_base",
                "args": [[], [[3, 5], [1, 4]]],
                "expected": [[1, 5]],
            },
        ],
        "hidden_cases": [
            {
                "label": "disjoint_two_groups",
                "args": [[[1, 2], [5, 6]], [[2, 3], [8, 9]]],
                "expected": [[1, 3], [5, 6], [8, 9]],
            },
            {
                "label": "both_empty",
                "args": [[], []],
                "expected": [],
            },
        ],
    },
    {
        "problem_id": "int_03_min_meeting_rooms_decoy",
        "family": "interval_processing",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "merge_span",
        "entry_point": "min_meeting_rooms",
        "statement": (
            "Write `min_meeting_rooms(meetings)` taking half-open intervals `[start, end)` "
            "(a meeting ending at t does NOT conflict with one starting at t) and returning the "
            "minimum number of concurrent rooms needed."
        ),
        "failed_attempts": [
            (
                "def min_meeting_rooms(meetings):\n"
                "    events = []\n"
                "    for s, e in meetings:\n"
                "        events.append((s, 1))\n"
                "        events.append((e, -1))\n"
                "    events.sort(key=lambda x: (x[0], -x[1]))\n"
                "    cur = best = 0\n"
                "    for _, d in events:\n"
                "        cur += d\n"
                "        best = max(best, cur)\n"
                "    return best\n"
            ),
            (
                "def min_meeting_rooms(meetings):\n"
                "    if not meetings:\n"
                "        return 0\n"
                "    xs = sorted(meetings)\n"
                "    rooms = 1\n"
                "    for i in range(1, len(xs)):\n"
                "        if xs[i][0] < xs[i - 1][1]:\n"
                "            rooms += 1\n"
                "    return rooms\n"
            ),
        ],
        "reference_with_helper": (
            "def min_meeting_rooms(meetings):\n"
            "    events = []\n"
            "    for s, e in meetings:\n"
            "        events.append((s, 1))\n"
            "        events.append((e, -1))\n"
            "    events.sort(key=lambda x: (x[0], x[1]))\n"
            "    cur = best = 0\n"
            "    for _, d in events:\n"
            "        cur += d\n"
            "        if cur > best:\n"
            "            best = cur\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "touching_half_open_tiebreak", "args": [[[0, 10], [10, 20]]], "expected": 1},
            {"label": "disjoint_clusters_no_room_release", "args": [[[1, 4], [2, 5], [10, 14], [11, 15]]], "expected": 2},
        ],
        "hidden_cases": [
            {"label": "empty", "args": [[]], "expected": 0},
            {"label": "three_concurrent", "args": [[[1, 10], [2, 7], [3, 19], [8, 12], [10, 20]]], "expected": 3},
        ],
    },
    # ------------------------------------------------------------------
    # Family 3: graph_traversal (helper: push_unvisited)
    # ------------------------------------------------------------------
    {
        "problem_id": "graph_01_shortest_path_unweighted",
        "family": "graph_traversal",
        "utility_regime": "useful_once",
        "helper_name": "push_unvisited",
        "entry_point": "shortest_path_len",
        "statement": (
            "Write `shortest_path_len(adj, src, dst)` taking adjacency list `adj` where `adj[u]` "
            "lists outgoing neighbors of node `u` (may contain cycles, self-loops, and duplicate "
            "entries) and returning the fewest edges from `src` to `dst`, or -1 if unreachable."
        ),
        "failed_attempts": [
            (
                "def shortest_path_len(adj, src, dst):\n"
                "    q = [(src, 0)]\n"
                "    steps = 0\n"
                "    while q and steps < 20:\n"
                "        node, d = q.pop(0)\n"
                "        steps += 1\n"
                "        if node == dst:\n"
                "            return d\n"
                "        for nxt in adj[node]:\n"
                "            q.append((nxt, d + 1))\n"
                "    return -1\n"
            ),
            (
                "def shortest_path_len(adj, src, dst):\n"
                "    q = [src]\n"
                "    visited = set()\n"
                "    dist = 0\n"
                "    while q:\n"
                "        nxt_level = []\n"
                "        for node in q:\n"
                "            if node == dst:\n"
                "                return dist\n"
                "            visited.add(node)\n"
                "            for nb in adj[node]:\n"
                "                if nb not in visited:\n"
                "                    nxt_level.append(nb)\n"
                "        if len(nxt_level) > 6:\n"
                "            return -1\n"
                "        q = nxt_level\n"
                "        dist += 1\n"
                "    return -1\n"
            ),
        ],
        "reference_with_helper": (
            "def shortest_path_len(adj, src, dst):\n"
            "    if src == dst:\n"
            "        return 0\n"
            "    visited = {src}\n"
            "    level = [src]\n"
            "    dist = 0\n"
            "    while level:\n"
            "        dist += 1\n"
            "        nxt_level = []\n"
            "        for node in level:\n"
            "            added = {OP}(nxt_level, visited, adj[node])\n"
            "            if added and dst in visited:\n"
            "                return dist\n"
            "        level = nxt_level\n"
            "    return -1\n"
        ),
        "public_cases": [
            {
                "label": "cycle_with_duplicate_edges",
                "args": [[[0, 1, 1, 2, 2], [0, 2, 2, 3], [1, 3, 3], [4], []], 0, 4],
                "expected": 3,
            },
            {
                "label": "unreachable_with_cycle",
                "args": [[[1, 0], [0, 1], []], 0, 2],
                "expected": -1,
            },
        ],
        "hidden_cases": [
            {"label": "same_src_dst", "args": [[[1], []], 0, 0], "expected": 0},
            {
                "label": "diamond_multi_edges",
                "args": [[[1, 1, 2, 2], [3, 3], [3, 3], [4], []], 0, 4],
                "expected": 3,
            },
        ],
    },
    {
        "problem_id": "graph_02_components_and_multisource",
        "family": "graph_traversal",
        "utility_regime": "repeatedly_useful",
        "helper_name": "push_unvisited",
        "entry_point": "component_count_and_reachable",
        "statement": (
            "Write `component_count_and_reachable(n, edges, sources)` for undirected graph on "
            "nodes `0..n-1` (edges may include duplicates and self-loops) returning `[components, "
            "reachable_from_sources]`."
        ),
        "failed_attempts": [
            (
                "def component_count_and_reachable(n, edges, sources):\n"
                "    adj = {i: [] for i in range(n)}\n"
                "    for u, v in edges:\n"
                "        adj[u].append(v)\n"
                "        adj[v].append(u)\n"
                "    visited = set()\n"
                "    comps = 0\n"
                "    for i in range(n):\n"
                "        if i not in visited:\n"
                "            comps += 1\n"
                "            q = [i]\n"
                "            while q:\n"
                "                u = q.pop()\n"
                "                visited.add(u)\n"
                "                for w in adj[u]:\n"
                "                    if w not in visited:\n"
                "                        q.append(w)\n"
                "    return [comps, len(sources)]\n"
            ),
            (
                "def component_count_and_reachable(n, edges, sources):\n"
                "    adj = {i: [] for i in range(n)}\n"
                "    for u, v in edges:\n"
                "        adj[u].append(v)\n"
                "        adj[v].append(u)\n"
                "    q = list(sources)\n"
                "    seen = set()\n"
                "    for u in q:\n"
                "        seen.add(u)\n"
                "        for w in adj[u]:\n"
                "            seen.add(w)\n"
                "    return [1, len(seen)]\n"
            ),
        ],
        "reference_with_helper": (
            "def component_count_and_reachable(n, edges, sources):\n"
            "    adj = {i: [] for i in range(n)}\n"
            "    for u, v in edges:\n"
            "        adj[u].append(v)\n"
            "        adj[v].append(u)\n"
            "    visited = set()\n"
            "    comps = 0\n"
            "    for i in range(n):\n"
            "        if i not in visited:\n"
            "            comps += 1\n"
            "            q = []\n"
            "            added = {OP}(q, visited, [i])\n"
            "            while q:\n"
            "                u = q.pop(0)\n"
            "                added = {OP}(q, visited, adj[u])\n"
            "    seen = set()\n"
            "    mq = []\n"
            "    added = {OP}(mq, seen, sources)\n"
            "    while mq:\n"
            "        u = mq.pop(0)\n"
            "        added = {OP}(mq, seen, adj[u])\n"
            "    return [comps, len(seen)]\n"
        ),
        "public_cases": [
            {
                "label": "two_components_multi_hop",
                "args": [5, [[0, 1], [1, 2], [1, 1], [3, 4], [3, 4]], [0]],
                "expected": [2, 3],
            },
            {
                "label": "duplicate_sources_and_isolated",
                "args": [4, [[0, 1]], [0, 0, 3]],
                "expected": [3, 3],
            },
        ],
        "hidden_cases": [
            {"label": "empty_sources", "args": [3, [[0, 1]], []], "expected": [2, 0]},
            {"label": "all_connected", "args": [4, [[0, 1], [1, 2], [2, 3], [3, 0]], [2]], "expected": [1, 4]},
        ],
    },
    {
        "problem_id": "graph_03_dag_longest_path_decoy",
        "family": "graph_traversal",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "push_unvisited",
        "entry_point": "dag_longest_path",
        "statement": (
            "Write `dag_longest_path(n, edges, src, dst)` for a weighted DAG on `0..n-1` where "
            "each edge is `[u, v, w]` (`w > 0`), returning the maximum total path weight from "
            "`src` to `dst`, or -1 if unreachable."
        ),
        "failed_attempts": [
            (
                "def dag_longest_path(n, edges, src, dst):\n"
                "    adj = {i: [] for i in range(n)}\n"
                "    for u, v, w in edges:\n"
                "        adj[u].append((v, w))\n"
                "    q = [(src, 0)]\n"
                "    visited = {src}\n"
                "    while q:\n"
                "        u, d = q.pop(0)\n"
                "        if u == dst:\n"
                "            return d\n"
                "        for v, w in adj[u]:\n"
                "            if v not in visited:\n"
                "                visited.add(v)\n"
                "                q.append((v, d + w))\n"
                "    return -1\n"
            ),
            (
                "def dag_longest_path(n, edges, src, dst):\n"
                "    adj = {i: [] for i in range(n)}\n"
                "    for u, v, w in edges:\n"
                "        adj[u].append((v, w))\n"
                "    dist = {src: 0}\n"
                "    q = [src]\n"
                "    seen = {src}\n"
                "    while q:\n"
                "        u = q.pop(0)\n"
                "        for v, w in adj[u]:\n"
                "            if v not in seen:\n"
                "                seen.add(v)\n"
                "                dist[v] = dist[u] + w\n"
                "                q.append(v)\n"
                "    return dist.get(dst, -1)\n"
            ),
        ],
        "reference_with_helper": (
            "def dag_longest_path(n, edges, src, dst):\n"
            "    adj = {i: [] for i in range(n)}\n"
            "    indeg = [0] * n\n"
            "    for u, v, w in edges:\n"
            "        adj[u].append((v, w))\n"
            "        indeg[v] += 1\n"
            "    topo = []\n"
            "    q = [i for i in range(n) if indeg[i] == 0]\n"
            "    while q:\n"
            "        u = q.pop(0)\n"
            "        topo.append(u)\n"
            "        for v, _ in adj[u]:\n"
            "            indeg[v] -= 1\n"
            "            if indeg[v] == 0:\n"
            "                q.append(v)\n"
            "    dist = {src: 0}\n"
            "    for u in topo:\n"
            "        if u not in dist:\n"
            "            continue\n"
            "        for v, w in adj[u]:\n"
            "            cand = dist[u] + w\n"
            "            if cand > dist.get(v, -1):\n"
            "                dist[v] = cand\n"
            "    return dist.get(dst, -1)\n"
        ),
        "public_cases": [
            {
                "label": "revisit_longer_path_required",
                "args": [4, [[0, 1, 2], [1, 2, 3], [2, 3, 4], [0, 3, 1]], 0, 3],
                "expected": 9,
            },
            {
                "label": "diamond_re_relaxation",
                "args": [4, [[0, 1, 1], [0, 2, 5], [1, 3, 1], [2, 1, 5]], 0, 3],
                "expected": 11,
            },
        ],
        "hidden_cases": [
            {"label": "unreachable", "args": [3, [[0, 1, 5]], 0, 2], "expected": -1},
            {"label": "src_eq_dst", "args": [2, [[0, 1, 3]], 0, 0], "expected": 0},
        ],
    },
]


def get_problem(problem_id: str) -> dict[str, Any]:
    for prob in DEV_PROBLEMS:
        if prob["problem_id"] == problem_id:
            return prob
    raise KeyError(f"Unknown problem_id: {problem_id}")


def verify_dev_family_suite(helper_token_id: int = 259) -> dict[str, Any]:
    """Verify every dev problem's failed attempts FAIL and references PASS both alias and ordinary arms."""
    rows = []
    for prob in DEV_PROBLEMS:
        all_cases = prob["public_cases"] + prob["hidden_cases"]
        # 1. Both saved pre-switch attempts must fail public cases.
        for idx, bad_src in enumerate(prob["failed_attempts"], start=1):
            bad_v = verify_candidate(
                bad_src,
                entry_point=prob["entry_point"],
                cases=prob["public_cases"],
                helper_name=None,
                binding=None,
                arm_uses_alias=False,
            )
            if bad_v["passed"]:
                raise AssertionError(f"{prob['problem_id']} failed_attempt #{idx} unexpectedly passed")

        # 2. Reference solution must pass ALL public + hidden cases under ordinary named helper.
        helper_name = prob["helper_name"]
        ref_ord = prob["reference_with_helper"].replace("{OP}", helper_name)
        v_ord = verify_candidate(
            ref_ord,
            entry_point=prob["entry_point"],
            cases=all_cases,
            helper_name=helper_name,
            binding=None,
            arm_uses_alias=False,
        )
        if not v_ord["passed"]:
            raise AssertionError(f"{prob['problem_id']} ordinary reference failed: {v_ord}")

        # 3. Reference solution must pass ALL public + hidden cases under <H0> single binding.
        reg = SingleBindRegistry()
        binding = reg.bind_once(helper_name, helper_token_id, HELPER_TOKEN_SYMBOL)
        ref_alias = prob["reference_with_helper"].replace("{OP}", HELPER_TOKEN_SYMBOL)
        v_alias = verify_candidate(
            ref_alias,
            entry_point=prob["entry_point"],
            cases=all_cases,
            helper_name=helper_name,
            binding=binding,
            arm_uses_alias=True,
        )
        if not v_alias["passed"]:
            raise AssertionError(f"{prob['problem_id']} alias reference failed: {v_alias}")

        if v_ord["syntax_mask"] and not v_ord["syntax_mask"]["mask_ok"]:
            raise AssertionError(f"{prob['problem_id']} ordinary reference broke syntax mask")
        if v_alias["syntax_mask"] and not v_alias["syntax_mask"]["mask_ok"]:
            raise AssertionError(f"{prob['problem_id']} alias reference broke syntax mask")

        # Confirm helper call multiplicity matches utility regime.
        calls = v_alias["syntactic_helper_calls"]
        if prob["utility_regime"] == "useful_once" and calls != 1:
            raise AssertionError(f"{prob['problem_id']} useful_once should have 1 call site, got {calls}")
        if prob["utility_regime"] == "repeatedly_useful" and calls < 2:
            raise AssertionError(f"{prob['problem_id']} repeatedly_useful should have >=2 call sites, got {calls}")
        if prob["utility_regime"] == "irrelevant_decoy" and calls != 0:
            raise AssertionError(f"{prob['problem_id']} irrelevant_decoy reference should have 0 helper calls, got {calls}")

        rows.append(
            {
                "problem_id": prob["problem_id"],
                "family": prob["family"],
                "utility_regime": prob["utility_regime"],
                "helper_name": helper_name,
                "public_cases": len(prob["public_cases"]),
                "hidden_cases": len(prob["hidden_cases"]),
                "ref_syntactic_helper_calls": calls,
                "ref_runtime_helper_calls": v_alias["runtime_helper_calls"],
                "ordinary_passed": v_ord["passed"],
                "alias_passed": v_alias["passed"],
            }
        )

    families = sorted({r["family"] for r in rows})
    regimes = sorted({r["utility_regime"] for r in rows})
    return {
        "total_problems": len(rows),
        "families": families,
        "utility_regimes": regimes,
        "all_verified": True,
        "problems": rows,
    }
