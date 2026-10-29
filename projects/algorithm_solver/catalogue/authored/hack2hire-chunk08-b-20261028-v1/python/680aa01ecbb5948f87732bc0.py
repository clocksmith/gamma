"""Hack2Hire 680aa01ecbb5948f87732bc0 (Shortest Path in Unweighted Graph) over an INFERRED spec; qualification unknown."""

def solve(n, edges, source, target):
    if source == target:
        return 0
    start = [0] * (n + 1)
    for u, v in edges:
        start[u + 1] += 1
        start[v + 1] += 1
    for i in range(n):
        start[i + 1] += start[i]
    fill = start[:]
    adj = [0] * start[n]
    for u, v in edges:
        adj[fill[u]] = v
        fill[u] += 1
        adj[fill[v]] = u
        fill[v] += 1
    dist = [-1] * n
    dist[source] = 0
    queue = [source]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for j in range(start[u], start[u + 1]):
            v = adj[j]
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                if v == target:
                    return dist[v]
                queue.append(v)
    return -1


class Solution:
    def shortestPath(self, n, edges, source, target):
        return solve(n, edges, source, target)
