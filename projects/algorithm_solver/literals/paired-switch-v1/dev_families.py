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


# Separate development families reserved for Stage 2 out-of-family Rung 2
# predictor validation (distinct from DEV_PROBLEMS above, and still strictly
# separate from untouched sealed holdout families).
DEV_VAL_PROBLEMS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Validation Family 4: string_parsing (helper: scan_quoted)
    # ------------------------------------------------------------------
    {
        "problem_id": "str_01_split_csv_quoted",
        "family": "string_parsing",
        "utility_regime": "useful_once",
        "helper_name": "scan_quoted",
        "entry_point": "split_csv_line",
        "statement": (
            "Write `split_csv_line(line)` splitting a single CSV line on commas outside double or "
            "single quotes while keeping quotes and backslash escapes intact inside each field."
        ),
        "failed_attempts": [
            (
                "def split_csv_line(line):\n"
                "    return line.split(',')\n"
            ),
            (
                "def split_csv_line(line):\n"
                "    fields = []\n"
                "    cur = []\n"
                "    in_q = False\n"
                "    for ch in line:\n"
                "        if ch == '\"':\n"
                "            in_q = not in_q\n"
                "            cur.append(ch)\n"
                "        elif ch == ',' and not in_q:\n"
                "            fields.append(''.join(cur))\n"
                "            cur = []\n"
                "        else:\n"
                "            cur.append(ch)\n"
                "    fields.append(''.join(cur))\n"
                "    return fields\n"
            ),
        ],
        "reference_with_helper": (
            "def split_csv_line(line):\n"
            "    fields = []\n"
            "    n = len(line)\n"
            "    start = 0\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        if line[i] in ('\"', \"'\"):\n"
            "            end = {OP}(line, i)\n"
            "            i = end\n"
            "        elif line[i] == ',':\n"
            "            fields.append(line[start:i])\n"
            "            i += 1\n"
            "            start = i\n"
            "        else:\n"
            "            i += 1\n"
            "    fields.append(line[start:])\n"
            "    return fields\n"
        ),
        "public_cases": [
            {
                "label": "escaped_quote_inside_field",
                "args": ['a,"b\\",c",d'],
                "expected": ["a", '"b\\",c"', "d"],
            },
            {
                "label": "escaped_backslash_before_closing_quote",
                "args": ['"a\\\\",b'],
                "expected": ['"a\\\\"', "b"],
            },
        ],
        "hidden_cases": [
            {"label": "plain_csv", "args": ["x,y,z"], "expected": ["x", "y", "z"]},
            {"label": "single_quoted_comma", "args": ["'a,b',c"], "expected": ["'a,b'", "c"]},
        ],
    },
    {
        "problem_id": "str_02_strip_comments_and_extract_strings",
        "family": "string_parsing",
        "utility_regime": "repeatedly_useful",
        "helper_name": "scan_quoted",
        "entry_point": "clean_and_extract_literals",
        "statement": (
            "Write `clean_and_extract_literals(src)` taking multi-line text `src`, stripping `#` "
            "comments that occur outside quoted strings on each line, and returning `[cleaned_src, "
            "quoted_literals]` where `quoted_literals` lists all quoted substrings from the cleaned text."
        ),
        "failed_attempts": [
            (
                "def clean_and_extract_literals(src):\n"
                "    out_lines = [ln.split('#', 1)[0] for ln in src.split('\\n')]\n"
                "    cleaned = '\\n'.join(out_lines)\n"
                "    return [cleaned, []]\n"
            ),
            (
                "def clean_and_extract_literals(src):\n"
                "    cleaned = src\n"
                "    lits = []\n"
                "    i = 0\n"
                "    while i < len(cleaned):\n"
                "        if cleaned[i] == '\"':\n"
                "            j = cleaned.find('\"', i + 1)\n"
                "            if j == -1:\n"
                "                break\n"
                "            lits.append(cleaned[i:j + 1])\n"
                "            i = j + 1\n"
                "        else:\n"
                "            i += 1\n"
                "    return [cleaned, lits]\n"
            ),
        ],
        "reference_with_helper": (
            "def clean_and_extract_literals(src):\n"
            "    out_lines = []\n"
            "    for ln in src.split('\\n'):\n"
            "        i = 0\n"
            "        cut = len(ln)\n"
            "        while i < len(ln):\n"
            "            if ln[i] in ('\"', \"'\"):\n"
            "                end = {OP}(ln, i)\n"
            "                i = end\n"
            "            elif ln[i] == '#':\n"
            "                cut = i\n"
            "                break\n"
            "            else:\n"
            "                i += 1\n"
            "        out_lines.append(ln[:cut])\n"
            "    cleaned = '\\n'.join(out_lines)\n"
            "    lits = []\n"
            "    k = 0\n"
            "    while k < len(cleaned):\n"
            "        if cleaned[k] in ('\"', \"'\"):\n"
            "            end = {OP}(cleaned, k)\n"
            "            lits.append(cleaned[k:end])\n"
            "            k = end\n"
            "        else:\n"
            "            k += 1\n"
            "    return [cleaned, lits]\n"
        ),
        "public_cases": [
            {
                "label": "hash_inside_escaped_quote_and_comment",
                "args": ['x = "a\\"#b" # trailing\ny = "c\\\\" # end'],
                "expected": ['x = "a\\"#b" \ny = "c\\\\" ', ['"a\\"#b"', '"c\\\\"']],
            },
            {
                "label": "comment_only_line",
                "args": ["# ignore \"not_a_lit\"\nz = 'ok'"],
                "expected": ["\nz = 'ok'", ["'ok'"]],
            },
        ],
        "hidden_cases": [
            {"label": "no_comments", "args": ['a = "hi"'], "expected": ['a = "hi"', ['"hi"']]},
            {"label": "empty", "args": [""], "expected": ["", []]},
        ],
    },
    {
        "problem_id": "str_03_balance_brackets_decoy",
        "family": "string_parsing",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "scan_quoted",
        "entry_point": "is_balanced_brackets",
        "statement": (
            "Write `is_balanced_brackets(s)` returning True if string `s` consisting only of "
            "brackets `()[]{}` is properly nested and balanced, else False."
        ),
        "failed_attempts": [
            (
                "def is_balanced_brackets(s):\n"
                "    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')\n"
            ),
            (
                "def is_balanced_brackets(s):\n"
                "    depth = 0\n"
                "    for ch in s:\n"
                "        if ch in '([{':\n"
                "            depth += 1\n"
                "        else:\n"
                "            depth -= 1\n"
                "            if depth < 0:\n"
                "                return False\n"
                "    return depth == 0\n"
            ),
        ],
        "reference_with_helper": (
            "def is_balanced_brackets(s):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for ch in s:\n"
            "        if ch in '([{':\n"
            "            stack.append(ch)\n"
            "        elif ch in pairs:\n"
            "            if not stack or stack[-1] != pairs[ch]:\n"
            "                return False\n"
            "            stack.pop()\n"
            "    return not stack\n"
        ),
        "public_cases": [
            {"label": "crossed_bracket_nesting", "args": ["([)]"], "expected": False},
            {"label": "mismatched_closing_bracket", "args": ["(]"], "expected": False},
        ],
        "hidden_cases": [
            {"label": "valid_nested", "args": ["{[()[]]}"], "expected": True},
            {"label": "empty_brackets", "args": [""], "expected": True},
        ],
    },
    # ------------------------------------------------------------------
    # Validation Family 5: window_aggregation (helper: prune_window)
    # ------------------------------------------------------------------
    {
        "problem_id": "win_01_sliding_max",
        "family": "window_aggregation",
        "utility_regime": "useful_once",
        "helper_name": "prune_window",
        "entry_point": "sliding_window_max",
        "statement": (
            "Write `sliding_window_max(nums, k)` returning the list of maximum values for every "
            "contiguous window of size `k` (`1 <= k <= len(nums)`), or `[]` if `nums` is empty."
        ),
        "failed_attempts": [
            (
                "def sliding_window_max(nums, k):\n"
                "    dq = []\n"
                "    out = []\n"
                "    for i, x in enumerate(nums):\n"
                "        while dq and nums[dq[-1]] < x:\n"
                "            dq.pop()\n"
                "        dq.append(i)\n"
                "        if i >= k - 1:\n"
                "            out.append(nums[dq[0]])\n"
                "    return out\n"
            ),
            (
                "def sliding_window_max(nums, k):\n"
                "    dq = []\n"
                "    out = []\n"
                "    for i in range(len(nums)):\n"
                "        if dq and dq[0] <= i - k:\n"
                "            dq.pop(0)\n"
                "        if dq and nums[dq[-1]] <= nums[i]:\n"
                "            dq.pop()\n"
                "        dq.append(i)\n"
                "        if i >= k - 1:\n"
                "            out.append(nums[dq[0]])\n"
                "    return out\n"
            ),
        ],
        "reference_with_helper": (
            "def sliding_window_max(nums, k):\n"
            "    if not nums:\n"
            "        return []\n"
            "    dq = []\n"
            "    out = []\n"
            "    for idx in range(len(nums)):\n"
            "        dq = {OP}(dq, nums, idx, idx - k + 1)\n"
            "        if idx >= k - 1:\n"
            "            out.append(nums[dq[0]])\n"
            "    return out\n"
        ),
        "public_cases": [
            {"label": "expired_front_maximum", "args": [[9, 1, 2, 3], 2], "expected": [9, 2, 3]},
            {"label": "multi_pop_monotonic_deque", "args": [[8, 4, 2, 7, 1], 3], "expected": [8, 7, 7]},
        ],
        "hidden_cases": [
            {"label": "equal_values_window", "args": [[3, 3, 1, 2, 2], 2], "expected": [3, 3, 2, 2]},
            {"label": "window_of_one", "args": [[4, -1, 5], 1], "expected": [4, -1, 5]},
        ],
    },
    {
        "problem_id": "win_02_dual_window_max_gap",
        "family": "window_aggregation",
        "utility_regime": "repeatedly_useful",
        "helper_name": "prune_window",
        "entry_point": "dual_window_max_diff",
        "statement": (
            "Write `dual_window_max_diff(nums, k1, k2)` (`1 <= k1 <= k2 <= len(nums)`) returning "
            "the maximum value of `max(nums[i-k2+1:i+1]) - max(nums[i-k1+1:i+1])` over all "
            "`i >= k2 - 1`."
        ),
        "failed_attempts": [
            (
                "def dual_window_max_diff(nums, k1, k2):\n"
                "    dq1, dq2 = [], []\n"
                "    best = 0\n"
                "    for i, x in enumerate(nums):\n"
                "        while dq1 and nums[dq1[-1]] <= x:\n"
                "            dq1.pop()\n"
                "        dq1.append(i)\n"
                "        while dq2 and nums[dq2[-1]] <= x:\n"
                "            dq2.pop()\n"
                "        dq2.append(i)\n"
                "        if i >= k2 - 1:\n"
                "            best = max(best, nums[dq2[0]] - nums[dq1[0]])\n"
                "    return best\n"
            ),
            (
                "def dual_window_max_diff(nums, k1, k2):\n"
                "    dq1, dq2 = [], []\n"
                "    best = 0\n"
                "    for i in range(len(nums)):\n"
                "        if dq1 and dq1[0] < i - k1 + 1:\n"
                "            dq1.pop(0)\n"
                "        if dq1 and nums[dq1[-1]] <= nums[i]:\n"
                "            dq1.pop()\n"
                "        dq1.append(i)\n"
                "        if dq2 and dq2[0] < i - k2 + 1:\n"
                "            dq2.pop(0)\n"
                "        if dq2 and nums[dq2[-1]] <= nums[i]:\n"
                "            dq2.pop()\n"
                "        dq2.append(i)\n"
                "        if i >= k2 - 1:\n"
                "            best = max(best, nums[dq2[0]] - nums[dq1[0]])\n"
                "    return best\n"
            ),
        ],
        "reference_with_helper": (
            "def dual_window_max_diff(nums, k1, k2):\n"
            "    dq1 = []\n"
            "    dq2 = []\n"
            "    best = 0\n"
            "    for idx in range(len(nums)):\n"
            "        dq1 = {OP}(dq1, nums, idx, idx - k1 + 1)\n"
            "        dq2 = {OP}(dq2, nums, idx, idx - k2 + 1)\n"
            "        if idx >= k2 - 1:\n"
            "            diff = nums[dq2[0]] - nums[dq1[0]]\n"
            "            if diff > best:\n"
            "                best = diff\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "expired_front_and_dual_deque", "args": [[10, 4, 2, 6, 1], 2, 4], "expected": 4},
            {"label": "stale_peak_drops_out", "args": [[20, 1, 1, 1, 5, 2], 2, 3], "expected": 19},
            {"label": "multi_pop_monotonic_deque_bug", "args": [[10, 9, 2, 1, 8], 3, 4], "expected": 1},
        ],
        "hidden_cases": [
            {"label": "equal_widths", "args": [[5, 2, 9, 1], 2, 2], "expected": 0},
            {"label": "descending", "args": [[10, 8, 6, 4, 2], 1, 3], "expected": 4},
        ],
    },
    {
        "problem_id": "win_03_fixed_window_sum_decoy",
        "family": "window_aggregation",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "prune_window",
        "entry_point": "max_window_sum",
        "statement": (
            "Write `max_window_sum(nums, k)` returning the maximum sum of any contiguous "
            "subarray of length `k` (`1 <= k <= len(nums)`). Values may be negative."
        ),
        "failed_attempts": [
            (
                "def max_window_sum(nums, k):\n"
                "    best = 0\n"
                "    cur = sum(nums[:k])\n"
                "    best = max(best, cur)\n"
                "    for i in range(k, len(nums)):\n"
                "        cur += nums[i] - nums[i - k]\n"
                "        best = max(best, cur)\n"
                "    return best\n"
            ),
            (
                "def max_window_sum(nums, k):\n"
                "    return sum(sorted(nums)[-k:])\n"
            ),
        ],
        "reference_with_helper": (
            "def max_window_sum(nums, k):\n"
            "    cur = sum(nums[:k])\n"
            "    best = cur\n"
            "    for i in range(k, len(nums)):\n"
            "        cur += nums[i] - nums[i - k]\n"
            "        if cur > best:\n"
            "            best = cur\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "all_negative_sum_init", "args": [[-5, -2, -8, -1], 2], "expected": -7},
            {"label": "non_contiguous_sort_bug", "args": [[9, -10, 8, -10, 7], 2], "expected": -1},
        ],
        "hidden_cases": [
            {"label": "mixed_positive", "args": [[1, 4, -2, 6, 3], 3], "expected": 8},
            {"label": "full_length", "args": [[-3, 2, -4], 3], "expected": -5},
        ],
    },
    # ------------------------------------------------------------------
    # Validation Family 6: grid_flood (helper: expand_grid)
    # ------------------------------------------------------------------
    {
        "problem_id": "grid_01_largest_island",
        "family": "grid_flood",
        "utility_regime": "useful_once",
        "helper_name": "expand_grid",
        "entry_point": "largest_island_area",
        "statement": (
            "Write `largest_island_area(grid)` returning the size of the largest 4-connected "
            "component of `1` cells in a binary 2D grid (`0` if none)."
        ),
        "failed_attempts": [
            (
                "def largest_island_area(grid):\n"
                "    rows, cols = len(grid), len(grid[0]) if grid else 0\n"
                "    visited = set()\n"
                "    best = 0\n"
                "    for r in range(rows):\n"
                "        for c in range(cols):\n"
                "            if grid[r][c] == 1 and (r, c) not in visited:\n"
                "                q = [(r, c)]\n"
                "                area = 0\n"
                "                while q:\n"
                "                    cr, cc = q.pop(0)\n"
                "                    visited.add((cr, cc))\n"
                "                    area += 1\n"
                "                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):\n"
                "                        nr, nc = cr + dr, cc + dc\n"
                "                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in visited:\n"
                "                            q.append((nr, nc))\n"
                "                best = max(best, area)\n"
                "    return best\n"
            ),
            (
                "def largest_island_area(grid):\n"
                "    rows, cols = len(grid), len(grid[0]) if grid else 0\n"
                "    best = 0\n"
                "    for r in range(rows):\n"
                "        for c in range(cols):\n"
                "            if grid[r][c] == 1:\n"
                "                cnt = 1\n"
                "                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):\n"
                "                    if grid[r + dr][c + dc] == 1:\n"
                "                        cnt += 1\n"
                "                best = max(best, cnt)\n"
                "    return best\n"
            ),
        ],
        "reference_with_helper": (
            "def largest_island_area(grid):\n"
            "    rows = len(grid)\n"
            "    cols = len(grid[0]) if rows else 0\n"
            "    visited = set()\n"
            "    best = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == 1 and (r, c) not in visited:\n"
            "                visited.add((r, c))\n"
            "                q = [[r, c]]\n"
            "                area = 0\n"
            "                while q:\n"
            "                    cr, cc = q.pop(0)\n"
            "                    area += 1\n"
            "                    added = {OP}(grid, q, visited, cr, cc)\n"
            "                if area > best:\n"
            "                    best = area\n"
            "    return best\n"
        ),
        "public_cases": [
            {
                "label": "square_2x2_duplicate_enqueue_bug",
                "args": [[[1, 1, 0], [1, 1, 0], [0, 0, 1]]],
                "expected": 4,
            },
            {
                "label": "corner_bounds_grid",
                "args": [[[1, 0], [0, 0]]],
                "expected": 1,
            },
        ],
        "hidden_cases": [
            {"label": "all_zeros", "args": [[[0, 0], [0, 0]]], "expected": 0},
            {"label": "u_shape", "args": [[[1, 0, 1], [1, 0, 1], [1, 1, 1]]], "expected": 7},
        ],
    },
    {
        "problem_id": "grid_02_islands_and_top_reach",
        "family": "grid_flood",
        "utility_regime": "repeatedly_useful",
        "helper_name": "expand_grid",
        "entry_point": "islands_and_top_reachable",
        "statement": (
            "Write `islands_and_top_reachable(grid)` returning `[island_count, top_reachable_cells]` "
            "where `island_count` is the number of 4-connected `1`-components and `top_reachable_cells` "
            "is the number of `1` cells reachable from any `1` cell on row 0."
        ),
        "failed_attempts": [
            (
                "def islands_and_top_reachable(grid):\n"
                "    rows, cols = len(grid), len(grid[0]) if grid else 0\n"
                "    visited = set()\n"
                "    islands = 0\n"
                "    for r in range(rows):\n"
                "        for c in range(cols):\n"
                "            if grid[r][c] == 1 and (r, c) not in visited:\n"
                "                islands += 1\n"
                "                q = [(r, c)]\n"
                "                visited.add((r, c))\n"
                "                while q:\n"
                "                    cr, cc = q.pop()\n"
                "                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):\n"
                "                        nr, nc = cr + dr, cc + dc\n"
                "                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in visited:\n"
                "                            visited.add((nr, nc))\n"
                "                            q.append((nr, nc))\n"
                "    top_cnt = sum(grid[0]) if rows else 0\n"
                "    return [islands, top_cnt]\n"
            ),
            (
                "def islands_and_top_reachable(grid):\n"
                "    rows, cols = len(grid), len(grid[0]) if grid else 0\n"
                "    seen = set()\n"
                "    for c in range(cols):\n"
                "        if grid[0][c] == 1:\n"
                "            seen.add((0, c))\n"
                "            if rows > 1 and grid[1][c] == 1:\n"
                "                seen.add((1, c))\n"
                "    return [1, len(seen)]\n"
            ),
        ],
        "reference_with_helper": (
            "def islands_and_top_reachable(grid):\n"
            "    rows = len(grid)\n"
            "    cols = len(grid[0]) if rows else 0\n"
            "    visited = set()\n"
            "    islands = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == 1 and (r, c) not in visited:\n"
            "                islands += 1\n"
            "                visited.add((r, c))\n"
            "                q = [[r, c]]\n"
            "                while q:\n"
            "                    cr, cc = q.pop(0)\n"
            "                    added = {OP}(grid, q, visited, cr, cc)\n"
            "    top_seen = set()\n"
            "    tq = []\n"
            "    if rows:\n"
            "        for c in range(cols):\n"
            "            if grid[0][c] == 1:\n"
            "                top_seen.add((0, c))\n"
            "                tq.append([0, c])\n"
            "    while tq:\n"
            "        cr, cc = tq.pop(0)\n"
            "        added = {OP}(grid, tq, top_seen, cr, cc)\n"
            "    return [islands, len(top_seen)]\n"
        ),
        "public_cases": [
            {
                "label": "multi_hop_top_island_and_detached",
                "args": [[[1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1]]],
                "expected": [2, 4],
            },
            {
                "label": "two_top_components",
                "args": [[[1, 0, 1], [1, 0, 1]]],
                "expected": [2, 4],
            },
        ],
        "hidden_cases": [
            {"label": "no_top_land", "args": [[[0, 0], [1, 1]]], "expected": [1, 0]},
            {"label": "all_zero", "args": [[[0, 0], [0, 0]]], "expected": [0, 0]},
        ],
    },
    {
        "problem_id": "grid_03_min_path_sum_dp_decoy",
        "family": "grid_flood",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "expand_grid",
        "entry_point": "min_grid_path_sum",
        "statement": (
            "Write `min_grid_path_sum(cost)` for a non-empty 2D grid of positive integers, "
            "returning the minimum total path cost from `(0, 0)` to `(R-1, C-1)` moving only "
            "right or down."
        ),
        "failed_attempts": [
            (
                "def min_grid_path_sum(cost):\n"
                "    r, c = 0, 0\n"
                "    rows, cols = len(cost), len(cost[0])\n"
                "    total = cost[0][0]\n"
                "    while (r, c) != (rows - 1, cols - 1):\n"
                "        if r == rows - 1:\n"
                "            c += 1\n"
                "        elif c == cols - 1:\n"
                "            r += 1\n"
                "        elif cost[r][c + 1] < cost[r + 1][c]:\n"
                "            c += 1\n"
                "        else:\n"
                "            r += 1\n"
                "        total += cost[r][c]\n"
                "    return total\n"
            ),
            (
                "def min_grid_path_sum(cost):\n"
                "    return sum(cost[0]) + sum(row[-1] for row in cost[1:])\n"
            ),
        ],
        "reference_with_helper": (
            "def min_grid_path_sum(cost):\n"
            "    rows, cols = len(cost), len(cost[0])\n"
            "    dp = [[0] * cols for _ in range(rows)]\n"
            "    dp[0][0] = cost[0][0]\n"
            "    for c in range(1, cols):\n"
            "        dp[0][c] = dp[0][c - 1] + cost[0][c]\n"
            "    for r in range(1, rows):\n"
            "        dp[r][0] = dp[r - 1][0] + cost[r][0]\n"
            "    for r in range(1, rows):\n"
            "        for c in range(1, cols):\n"
            "            dp[r][c] = cost[r][c] + min(dp[r - 1][c], dp[r][c - 1])\n"
            "    return dp[-1][-1]\n"
        ),
        "public_cases": [
            {
                "label": "greedy_trap_dp_cost",
                "args": [[[1, 2, 100], [5, 1, 1], [100, 1, 1]]],
                "expected": 6,
            },
            {
                "label": "weighted_border_not_optimal",
                "args": [[[1, 3, 1], [1, 5, 1], [4, 2, 1]]],
                "expected": 7,
            },
        ],
        "hidden_cases": [
            {"label": "single_cell", "args": [[[9]]], "expected": 9},
            {"label": "rect_grid", "args": [[[1, 2, 3], [4, 5, 6]]], "expected": 12},
        ],
    },
]


ALL_DEV_PROBLEMS: list[dict[str, Any]] = DEV_PROBLEMS + DEV_VAL_PROBLEMS


def get_dev_split(split_name: str = "train") -> list[dict[str, Any]]:
    if split_name == "train":
        return list(DEV_PROBLEMS)
    if split_name == "val":
        return list(DEV_VAL_PROBLEMS)
    if split_name == "all":
        return list(ALL_DEV_PROBLEMS)
    raise ValueError(f"Unknown dev split: {split_name!r} (expected 'train', 'val', or 'all')")


def get_problem(problem_id: str) -> dict[str, Any]:
    for prob in ALL_DEV_PROBLEMS:
        if prob["problem_id"] == problem_id:
            return prob
    raise KeyError(f"Unknown problem_id: {problem_id}")


def verify_dev_family_suite(
    helper_token_id: int = 259,
    problems: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Verify every dev problem's failed attempts FAIL and references PASS both alias and ordinary arms."""
    target_problems = list(ALL_DEV_PROBLEMS if problems is None else problems)
    rows = []
    for prob in target_problems:
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
