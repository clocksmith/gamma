"""Algorithm patterns: tag mapping, short guidance, and fill-in templates.

Each template is a working skeleton with explicit HOLE comments. Route 4 shows
the model the templates for the predicted patterns; the model fills the holes
for the specific problem. The set is deliberately small; "unknown" is a valid
classifier output and then no template is shown.
"""

from __future__ import annotations

PATTERNS: dict[str, dict] = {
    "hash_counting": {
        "tags": ["Hash Table", "Counting", "hashing"],
        "guidance": "Count or index elements in a dict/Counter for O(1) lookups; look for complements or seen states.",
        "template": '''
from collections import Counter, defaultdict

def solve(items):
    seen = {}                      # HOLE: what maps to what (value -> index, prefix -> count, ...)
    for i, x in enumerate(items):
        need = x                   # HOLE: the key that completes an answer with x
        if need in seen:
            pass                   # HOLE: record / return the answer
        seen[x] = i                # HOLE: update the map after checking
    return None                    # HOLE: final answer
''',
    },
    "two_pointers": {
        "tags": ["Two Pointers"],
        "guidance": "Move two indices toward each other (sorted input) or same direction (read/write, fast/slow).",
        "template": '''
def solve(a):
    a.sort()                       # HOLE: sort only if order does not matter
    i, j = 0, len(a) - 1
    best = None
    while i < j:
        s = a[i] + a[j]            # HOLE: quantity defined by the pair
        if s == 0:                 # HOLE: target condition
            best = (i, j)          # HOLE: record answer
            i += 1; j -= 1
        elif s < 0:                # HOLE: which side to move
            i += 1
        else:
            j -= 1
    return best
''',
    },
    "sliding_window": {
        "tags": ["Sliding Window"],
        "guidance": "Grow the right edge; shrink the left edge while the window violates the constraint; track the best window.",
        "template": '''
from collections import defaultdict

def solve(s, k):
    count = defaultdict(int)
    left = 0
    best = 0
    for right, ch in enumerate(s):
        count[ch] += 1             # HOLE: add s[right] to window state
        while len(count) > k:      # HOLE: window-invalid condition
            count[s[left]] -= 1    # HOLE: remove s[left] from window state
            if count[s[left]] == 0:
                del count[s[left]]
            left += 1
        best = max(best, right - left + 1)  # HOLE: what to optimize
    return best
''',
    },
    "binary_search": {
        "tags": ["Binary Search"],
        "guidance": "Binary search on an index or on the answer value with a monotone feasibility check.",
        "template": '''
def solve(nums, limit):
    def feasible(x):               # HOLE: monotone predicate on the answer x
        return sum((v + x - 1) // x for v in nums) <= limit

    lo, hi = 1, max(nums)          # HOLE: answer range [lo, hi]
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):          # smallest x that is feasible
            hi = mid
        else:
            lo = mid + 1
    return lo
''',
    },
    "monotonic_stack": {
        "tags": ["Monotonic Stack", "Stack", "Monotonic Queue"],
        "guidance": "Keep a stack of indices with monotone values to find next/previous greater or smaller elements.",
        "template": '''
def solve(a):
    n = len(a)
    answer = [-1] * n              # HOLE: default when no element qualifies
    stack = []                     # indices with decreasing a[...]
    for i, x in enumerate(a):
        while stack and a[stack[-1]] < x:   # HOLE: pop condition (< for next greater)
            j = stack.pop()
            answer[j] = i          # HOLE: what to store for j (index, distance, value)
        stack.append(i)
    return answer
''',
    },
    "heap": {
        "tags": ["Heap (Priority Queue)", "Ordered Set"],
        "guidance": "Use heapq for repeated min/max extraction, top-k, merging sorted streams, or scheduling.",
        "template": '''
import heapq

def solve(items, k):
    heap = []
    for x in items:
        heapq.heappush(heap, x)    # HOLE: key to order by (negate for max-heap)
        if len(heap) > k:          # HOLE: size bound / eviction rule
            heapq.heappop(heap)
    return heap[0]                 # HOLE: answer from heap contents
''',
    },
    "graph_traversal": {
        "tags": ["Breadth-First Search", "Depth-First Search", "Graph", "Topological Sort", "Tree", "Binary Tree",
                 "dfs and similar", "graphs", "trees"],
        "guidance": "Build adjacency lists; BFS for fewest steps / levels, DFS for components, Kahn's algorithm for order.",
        "template": '''
from collections import deque, defaultdict

def solve(n, edges, start):
    graph = defaultdict(list)
    for u, v in edges:             # HOLE: directed or undirected?
        graph[u].append(v)
        graph[v].append(u)
    dist = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in dist:      # HOLE: extra state in the visited key if needed
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist                    # HOLE: answer from distances / visited set
''',
    },
    "shortest_path": {
        "tags": ["Shortest Path", "shortest paths"],
        "guidance": "Dijkstra with a heap for non-negative weights; Bellman-Ford or BFS variants otherwise.",
        "template": '''
import heapq
from collections import defaultdict

def solve(n, edges, src):
    graph = defaultdict(list)
    for u, v, w in edges:          # HOLE: edge direction and weight
        graph[u].append((v, w))
    dist = [float("inf")] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w             # HOLE: relaxation rule
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist                    # HOLE: answer from dist
''',
    },
    "dynamic_programming": {
        "tags": ["Dynamic Programming", "Memoization", "dp"],
        "guidance": "Define the state, the transition and the base case; memoize recursion or fill a table in dependency order.",
        "template": '''
from functools import cache

def solve(a):
    n = len(a)

    @cache
    def best(i):                   # HOLE: state (index, remaining budget, last choice, ...)
        if i >= n:                 # HOLE: base case
            return 0
        take = a[i] + best(i + 2)  # HOLE: transitions
        skip = best(i + 1)
        return max(take, skip)     # HOLE: combine (max/min/sum mod p)

    return best(0)
''',
    },
    "union_find": {
        "tags": ["Union Find", "dsu"],
        "guidance": "Disjoint-set union with path compression to merge groups and query connectivity.",
        "template": '''
def solve(n, pairs):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = n
    for a, b in pairs:             # HOLE: which elements to union
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            components -= 1
    return components              # HOLE: answer from the partition
''',
    },
    "prefix_sum": {
        "tags": ["Prefix Sum"],
        "guidance": "Precompute prefix sums for O(1) range queries; pair with a hash map to count subarrays with a target sum.",
        "template": '''
from collections import defaultdict

def solve(nums, target):
    seen = defaultdict(int)
    seen[0] = 1
    total = 0
    count = 0
    for x in nums:
        total += x                 # HOLE: running quantity (sum, parity, mod k)
        count += seen[total - target]  # HOLE: which earlier prefix completes a valid range
        seen[total] += 1
    return count
''',
    },
    "greedy_sorting": {
        "tags": ["Greedy", "Sorting", "greedy", "sortings"],
        "guidance": "Sort by the key that makes a local choice safe (end time, ratio, deadline) and take greedily.",
        "template": '''
def solve(intervals):
    intervals.sort(key=lambda iv: iv[1])   # HOLE: sort key that makes greedy safe
    chosen = 0
    last_end = float("-inf")
    for start, end in intervals:
        if start >= last_end:      # HOLE: compatibility rule
            chosen += 1
            last_end = end
    return chosen                  # HOLE: answer
''',
    },
    "backtracking": {
        "tags": ["Backtracking", "brute force", "bitmasks", "Bitmask"],
        "guidance": "Enumerate choices recursively with pruning; undo each choice after exploring it.",
        "template": '''
def solve(candidates, target):
    results = []
    path = []

    def explore(start, remaining):
        if remaining == 0:         # HOLE: complete-solution condition
            results.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:   # HOLE: pruning rule
                break
            path.append(candidates[i])
            explore(i, remaining - candidates[i])   # HOLE: reuse allowed? i or i + 1
            path.pop()

    candidates.sort()
    explore(0, target)
    return results
''',
    },
}

TAG_TO_PATTERNS: dict[str, list[str]] = {}
for _name, _spec in PATTERNS.items():
    for _tag in _spec["tags"]:
        TAG_TO_PATTERNS.setdefault(_tag.lower(), []).append(_name)


def patterns_for_tags(tags: list[str]) -> list[str]:
    out: list[str] = []
    for tag in tags:
        for name in TAG_TO_PATTERNS.get(tag.lower(), []):
            if name not in out:
                out.append(name)
    return out


def render(names: list[str]) -> str:
    blocks = []
    for name in names:
        spec = PATTERNS[name]
        blocks.append(f"Pattern: {name}\nWhen it fits: {spec['guidance']}\nTemplate:\n```python{spec['template']}```")
    return "\n\n".join(blocks)
