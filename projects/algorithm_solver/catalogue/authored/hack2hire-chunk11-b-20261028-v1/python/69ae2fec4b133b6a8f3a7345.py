"""Hack2Hire 69ae2fec4b133b6a8f3a7345 (Largest Group of Mutual Strangers) over an INFERRED spec; qualification unknown."""


def solve(n, connections):
    degree = [0] * (n + 1)
    for a, b in connections:
        degree[a + 1] += 1
        degree[b + 1] += 1
    for i in range(n):
        degree[i + 1] += degree[i]  # prefix sums: adjacency offsets
    fill = degree[:]
    adjacency = [0] * (2 * len(connections))
    for a, b in connections:
        adjacency[fill[a]] = b; fill[a] += 1
        adjacency[fill[b]] = a; fill[b] += 1
    parent = [-2] * n
    take = [1] * n
    skip = [0] * n
    best = 0
    for root in range(n):
        if parent[root] != -2:
            continue
        parent[root] = -1
        order = [root]
        k = 0
        while k < len(order):
            v = order[k]
            k += 1
            for e in range(degree[v], degree[v + 1]):
                w = adjacency[e]
                if parent[w] == -2:
                    parent[w] = v
                    order.append(w)
        for v in reversed(order):
            p = parent[v]
            if p >= 0:
                take[p] += skip[v]
                skip[p] += max(take[v], skip[v])
        best += max(take[root], skip[root])
    return best


class Solution:
    def largestStrangerGroup(self, n, connections):
        return solve(n, connections)
