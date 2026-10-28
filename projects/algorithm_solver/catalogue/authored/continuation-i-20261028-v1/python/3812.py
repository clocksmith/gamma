def solve(n, edges, start, target):
    graph = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        graph[u].append((v, i))
        graph[v].append((u, i))
    parent = [-1] * n
    parent_edge = [-1] * n
    parent[0] = 0
    order = [0]
    for u in order:
        for v, edge in graph[u]:
            if v != parent[u]:
                parent[v] = u
                parent_edge[v] = edge
                order.append(v)
    mismatch = [int(x != y) for x, y in zip(start, target)]
    chosen = [False] * (n - 1)
    for v in reversed(order[1:]):
        if mismatch[v]:
            chosen[parent_edge[v]] = True
            mismatch[parent[v]] ^= 1
    if mismatch[0]:
        return [-1]
    return [i for i, selected in enumerate(chosen) if selected]


class Solution:
    def minimumFlips(self, n, edges, start, target):
        return solve(n, edges, start, target)
