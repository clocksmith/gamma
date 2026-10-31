"""Original frontend 3249 variant; qualification unknown."""


def solve(edges) -> int:
    n = len(edges) + 1
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    order = [0]
    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    sz = [1] * n
    good = 0
    for u in reversed(order):
        first = -1
        ok = True
        for v in adj[u]:
            if v != parent[u]:
                sz[u] += sz[v]
                if first == -1:
                    first = sz[v]
                elif sz[v] != first:
                    ok = False
        if ok:
            good += 1
    return good


countGoodNodes = solve


class Solution:
    def countGoodNodes(self, edges) -> int:
        return solve(edges)
