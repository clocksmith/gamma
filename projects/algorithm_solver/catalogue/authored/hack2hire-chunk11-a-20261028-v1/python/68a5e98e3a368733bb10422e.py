"""Hack2Hire 68a5e98e3a368733bb10422e (Find Path with Minimal Bottleneck) over an INFERRED spec; qualification unknown."""


def solve(n, edges, k):
    weights = sorted({w for _, _, w in edges})
    adjacency = [[] for _ in range(n + 1)]
    for u, v, w in edges:
        adjacency[u].append((v, w))
        adjacency[v].append((u, w))

    def reachable(limit):  # breadth-first search over edges not heavier than limit, at most k hops
        dist = [-1] * (n + 1)
        dist[1] = 0
        queue, i = [1], 0
        while i < len(queue):
            x = queue[i]
            i += 1
            if dist[x] == k:
                continue
            for y, w in adjacency[x]:
                if w <= limit and dist[y] < 0:
                    if y == n:
                        return True
                    dist[y] = dist[x] + 1
                    queue.append(y)
        return False

    lo, hi, answer = 0, len(weights) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if reachable(weights[mid]):
            answer, hi = weights[mid], mid - 1
        else:
            lo = mid + 1
    return answer


class Solution:
    def findMinimalBottleneck(self, n, edges, k):
        return solve(n, edges, k)
