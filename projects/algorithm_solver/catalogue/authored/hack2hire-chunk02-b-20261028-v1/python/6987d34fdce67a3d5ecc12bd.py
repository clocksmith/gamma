"""Original Hack2Hire 6987d34fdce67a3d5ecc12bd variant over an INFERRED specification; qualification unknown."""


def solve(n, treeFrom, treeTo, x, y, z):
    adjacent = [[] for _ in range(n)]
    for u, v in zip(treeFrom, treeTo):
        adjacent[u].append(v)
        adjacent[v].append(u)

    def bfs(source):
        dist = [-1] * n
        dist[source] = 0
        queue = [source]
        for u in queue:
            for v in adjacent[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return dist
    dx, dy, dz = bfs(x), bfs(y), bfs(z)
    count = 0
    for u in range(n):
        a, b, c = sorted((dx[u], dy[u], dz[u]))
        if a * a + b * b == c * c:
            count += 1
    return count


class Solution:
    def countPythagoreanNodes(self, n, treeFrom, treeTo, x, y, z):
        return solve(n, treeFrom, treeTo, x, y, z)
