"""Reusable algorithm components with written contracts and unit tests.

Each component is self-contained Python (no hidden state, 0-based indexing,
inputs never mutated unless the contract says so). The contract states input
types, preconditions, the result, and complexity. Unit tests compare each
component with a brute-force reference on random inputs; they establish
tested contracts, not formal proofs. Components were chosen from index
problems only; the held-out solving problems were not consulted.
"""

from __future__ import annotations

COMPONENTS: dict[str, dict] = {}


def component(name: str, contract: str, source: str) -> None:
    COMPONENTS[name] = {"name": name, "contract": contract.strip(), "source": source.strip() + "\n"}


component("dsu", """
c_DSU(n): disjoint sets over 0..n-1.
  .find(x) -> root; .union(a, b) -> True if merged; .size(x) -> set size; .count -> number of sets.
  Path compression + union by size; near-O(1) amortized per operation.
""", """
class c_DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.sz = [1] * n
        self.count = n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.sz[ra] += self.sz[rb]
        self.count -= 1
        return True

    def size(self, x):
        return self.sz[self.find(x)]
""")

component("fenwick", """
c_Fenwick(n): prefix sums over positions 0..n-1, all zero initially.
  .add(i, delta); .prefix(i) -> sum of positions [0, i); .range(l, r) -> sum of [l, r). O(log n) each.
""", """
class c_Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, i, delta):
        i += 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix(self, i):
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total

    def range(self, l, r):
        return self.prefix(r) - self.prefix(l)
""")

component("segtree", """
c_SegTree(values, op, identity): op must be associative with identity (e.g. min/inf, max/-inf, add/0).
  .update(i, value) sets position i; .query(l, r) -> op over [l, r) (identity if empty). O(log n).
""", """
class c_SegTree:
    def __init__(self, values, op, identity):
        self.n = len(values)
        self.op = op
        self.identity = identity
        self.tree = [identity] * (2 * self.n)
        self.tree[self.n:] = list(values)
        for i in range(self.n - 1, 0, -1):
            self.tree[i] = op(self.tree[2 * i], self.tree[2 * i + 1])

    def update(self, i, value):
        i += self.n
        self.tree[i] = value
        while i > 1:
            i //= 2
            self.tree[i] = self.op(self.tree[2 * i], self.tree[2 * i + 1])

    def query(self, l, r):
        left = right = self.identity
        l += self.n
        r += self.n
        while l < r:
            if l & 1:
                left = self.op(left, self.tree[l])
                l += 1
            if r & 1:
                r -= 1
                right = self.op(self.tree[r], right)
            l //= 2
            r //= 2
        return self.op(left, right)
""")

component("sieve", """
c_sieve(n) -> list is_prime of length n+1 (is_prime[0] = is_prime[1] = False). O(n log log n).
c_primes(n) -> sorted list of primes <= n.
""", """
def c_sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = False
    if n >= 1:
        is_prime[1] = False
    i = 2
    while i * i <= n:
        if is_prime[i]:
            is_prime[i * i::i] = [False] * len(range(i * i, n + 1, i))
        i += 1
    return is_prime


def c_primes(n):
    return [i for i, p in enumerate(c_sieve(n)) if p]
""")

component("modcomb", """
c_ModComb(n, mod): factorial tables up to n for prime mod.
  .ncr(a, b) -> C(a, b) mod p (0 if b < 0 or b > a); .fact[a]; .inv_fact[a]. O(n) build, O(1) query.
""", """
class c_ModComb:
    def __init__(self, n, mod=10**9 + 7):
        self.mod = mod
        self.fact = [1] * (n + 1)
        for i in range(1, n + 1):
            self.fact[i] = self.fact[i - 1] * i % mod
        self.inv_fact = [1] * (n + 1)
        self.inv_fact[n] = pow(self.fact[n], mod - 2, mod)
        for i in range(n, 0, -1):
            self.inv_fact[i - 1] = self.inv_fact[i] * i % mod

    def ncr(self, a, b):
        if b < 0 or b > a:
            return 0
        return self.fact[a] * self.inv_fact[b] % self.mod * self.inv_fact[a - b] % self.mod
""")

component("lis", """
c_lis_length(seq, strict=True) -> length of the longest increasing subsequence
  (strictly increasing if strict, else non-decreasing). O(n log n).
""", """
def c_lis_length(seq, strict=True):
    from bisect import bisect_left, bisect_right
    tails = []
    for x in seq:
        i = bisect_left(tails, x) if strict else bisect_right(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
""")

component("kmp", """
c_prefix_function(s) -> pi where pi[i] = length of the longest proper border of s[:i+1]. O(n).
c_find_all(text, pattern) -> sorted start indices of pattern in text (pattern non-empty). O(n + m).
""", """
def c_prefix_function(s):
    pi = [0] * len(s)
    for i in range(1, len(s)):
        k = pi[i - 1]
        while k and s[i] != s[k]:
            k = pi[k - 1]
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return pi


def c_find_all(text, pattern):
    combined = list(pattern) + [None] + list(text)
    pi = c_prefix_function(combined)
    m = len(pattern)
    return [i - 2 * m for i in range(len(combined)) if pi[i] == m]
""")

component("zfunc", """
c_z_function(s) -> z where z[i] = length of the longest common prefix of s and s[i:], z[0] = len(s). O(n).
""", """
def c_z_function(s):
    n = len(s)
    z = [0] * n
    if n:
        z[0] = n
    l = r = 0
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > r:
            l, r = i, i + z[i]
    return z
""")

component("graph", """
c_adjacency(n, edges, directed=False, weighted=False) -> adjacency list; edges are (u, v) or (u, v, w).
c_bfs(n, adj, sources) -> dist list (-1 if unreachable), unweighted.
c_dijkstra(n, adj, sources) -> dist list (inf if unreachable); adj from weighted=True; weights >= 0.
c_topo(n, adj) -> topological order list, or None if the directed graph has a cycle.
""", """
def c_adjacency(n, edges, directed=False, weighted=False):
    adj = [[] for _ in range(n)]
    for edge in edges:
        if weighted:
            u, v, w = edge
            adj[u].append((v, w))
            if not directed:
                adj[v].append((u, w))
        else:
            u, v = edge[0], edge[1]
            adj[u].append(v)
            if not directed:
                adj[v].append(u)
    return adj


def c_bfs(n, adj, sources):
    from collections import deque
    dist = [-1] * n
    queue = deque()
    for s in sources:
        if dist[s] == -1:
            dist[s] = 0
            queue.append(s)
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def c_dijkstra(n, adj, sources):
    import heapq
    dist = [float("inf")] * n
    heap = []
    for s in sources:
        dist[s] = 0
        heap.append((0, s))
    heapq.heapify(heap)
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def c_topo(n, adj):
    indeg = [0] * n
    for u in range(n):
        for v in adj[u]:
            indeg[v] += 1
    order = [u for u in range(n) if indeg[u] == 0]
    head = 0
    while head < len(order):
        u = order[head]
        head += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                order.append(v)
    return order if len(order) == n else None
""")

component("grid", """
c_grid_bfs(grid, sources, passable) -> dict {(r, c): steps} over 4-neighbour moves on cells where
  passable(grid[r][c]) is true; sources is an iterable of (r, c). Unreached cells are absent.
c_neighbors4(r, c, rows, cols) -> in-bounds 4-neighbours.
""", """
def c_neighbors4(r, c, rows, cols):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def c_grid_bfs(grid, sources, passable):
    from collections import deque
    rows, cols = len(grid), len(grid[0]) if grid else 0
    dist = {}
    queue = deque()
    for cell in sources:
        cell = tuple(cell)
        if cell not in dist:
            dist[cell] = 0
            queue.append(cell)
    while queue:
        r, c = queue.popleft()
        for nr, nc in c_neighbors4(r, c, rows, cols):
            if (nr, nc) not in dist and passable(grid[nr][nc]):
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    return dist
""")

component("kruskal", """
c_kruskal(n, edges) -> (total_weight, chosen_edges, components) for edges (u, v, w); minimum spanning
  forest. Requires component dsu.
""", """
def c_kruskal(n, edges):
    dsu = c_DSU(n)
    total = 0
    chosen = []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if dsu.union(u, v):
            total += w
            chosen.append((u, v, w))
    return total, chosen, dsu.count
""")

component("binsearch", """
c_first_true(lo, hi, pred) -> smallest x in [lo, hi] with pred(x) true, assuming pred is monotone
  false...true; returns hi + 1 if none. O(log(hi - lo)) calls to pred.
c_last_true(lo, hi, pred) -> largest x in [lo, hi] with pred(x) true for monotone true...false; lo - 1 if none.
""", """
def c_first_true(lo, hi, pred):
    left, right = lo, hi + 1
    while left < right:
        mid = (left + right) // 2
        if pred(mid):
            right = mid
        else:
            left = mid + 1
    return left


def c_last_true(lo, hi, pred):
    left, right = lo - 1, hi
    while left < right:
        mid = (left + right + 1) // 2
        if pred(mid):
            left = mid
        else:
            right = mid - 1
    return left
""")

component("monostack", """
c_next_index(seq, better) -> nxt where nxt[i] = smallest j > i with better(seq[j], seq[i]) true, else len(seq).
c_prev_index(seq, better) -> prv where prv[i] = largest j < i with better(seq[j], seq[i]) true, else -1.
  `better` must be a strict or non-strict comparison (e.g. lambda a, b: a > b). O(n).
""", """
def c_next_index(seq, better):
    n = len(seq)
    nxt = [n] * n
    stack = []
    for j, x in enumerate(seq):
        while stack and better(x, seq[stack[-1]]):
            nxt[stack.pop()] = j
        stack.append(j)
    return nxt


def c_prev_index(seq, better):
    n = len(seq)
    prv = [-1] * n
    stack = []
    for j in range(n - 1, -1, -1):
        x = seq[j]
        while stack and better(x, seq[stack[-1]]):
            prv[stack.pop()] = j
        stack.append(j)
    return prv
""")

component("prefix", """
c_prefix_sums(seq) -> p of length len(seq)+1 with p[i] = sum(seq[:i]).
c_prefix_2d(grid) -> P with P[r][c] = sum of grid[:r][:c]; c_rect_sum(P, r1, c1, r2, c2) -> sum of rows
  [r1, r2), cols [c1, c2).
""", """
def c_prefix_sums(seq):
    out = [0]
    for x in seq:
        out.append(out[-1] + x)
    return out


def c_prefix_2d(grid):
    rows, cols = len(grid), len(grid[0]) if grid else 0
    P = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(rows):
        for c in range(cols):
            P[r + 1][c + 1] = P[r][c + 1] + P[r + 1][c] - P[r][c] + grid[r][c]
    return P


def c_rect_sum(P, r1, c1, r2, c2):
    return P[r2][c2] - P[r1][c2] - P[r2][c1] + P[r1][c1]
""")

component("intervals", """
c_merge_intervals(intervals) -> merged, sorted, non-overlapping [start, end] lists; intervals touching at
  an endpoint are merged.
""", """
def c_merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""")

component("trie", """
c_Trie(): .insert(word) ; .count_prefix(prefix) -> number of inserted words with that prefix;
  .contains(word) -> bool. O(len) each.
""", """
class c_Trie:
    def __init__(self):
        self.children = [{}]
        self.passing = [0]
        self.ending = [0]

    def insert(self, word):
        node = 0
        self.passing[0] += 1
        for ch in word:
            nxt = self.children[node].get(ch)
            if nxt is None:
                nxt = len(self.children)
                self.children[node][ch] = nxt
                self.children.append({})
                self.passing.append(0)
                self.ending.append(0)
            node = nxt
            self.passing[node] += 1
        self.ending[node] += 1

    def _walk(self, prefix):
        node = 0
        for ch in prefix:
            node = self.children[node].get(ch)
            if node is None:
                return None
        return node

    def count_prefix(self, prefix):
        node = self._walk(prefix)
        return 0 if node is None else self.passing[node]

    def contains(self, word):
        node = self._walk(word)
        return node is not None and self.ending[node] > 0
""")

component("structures", """
Conversions for LeetCode linked lists and binary trees (ListNode / TreeNode are provided by the harness).
c_list_values(head) -> list of values; c_list_from(values) -> head (None if empty).
c_tree_values(root) -> LeetCode level-order list (trailing None trimmed); c_tree_from(values) -> root.
""", """
def c_list_values(head):
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def c_list_from(values):
    head = None
    for v in reversed(list(values)):
        head = ListNode(v, head)
    return head


def c_tree_values(root):
    out, queue = [], [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def c_tree_from(values):
    values = list(values)
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue, i = [root], 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root
""")

COMPONENT_DEPENDENCIES = {"kruskal": ["dsu"]}


def provided_names() -> dict[str, str]:
    """Map each top-level c_* function/class to the component that defines it."""
    import ast

    out = {}
    for name, spec in COMPONENTS.items():
        for node in ast.parse(spec["source"]).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                out[node.name] = name
    return out


def referenced(source: str) -> list[str]:
    """Components whose c_* names appear in the given hole text."""
    import re

    names = provided_names()
    return sorted({names[m] for m in re.findall(r"\bc_\w+", source) if m in names})


def resolve(names: list[str]) -> list[str]:
    out: list[str] = []
    for name in names:
        if name not in COMPONENTS:
            raise KeyError(f"unknown component: {name}")
        for dep in COMPONENT_DEPENDENCIES.get(name, []):
            if dep not in out:
                out.append(dep)
        if name not in out:
            out.append(name)
    return out


def catalog_text() -> str:
    return "\n\n".join(f"[{c['name']}]\n{c['contract']}" for c in COMPONENTS.values())
