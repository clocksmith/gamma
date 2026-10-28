"""743. Network Delay Time (Medium).

Specification: https://leetcode.com/problems/network-delay-time/description/
"""


def solve(times: list[list[int]], n: int, k: int) -> int:
    graph = {}
    for frm, to, weight in times:
        graph.setdefault(frm, []).append((to, weight))
    dist = [float('inf')] * (n + 1)
    dist[k] = 0
    visited = set()
    for _step in range(n):
        node = -1
        best = float('inf')
        for i in range(1, n + 1):
            if i not in visited and dist[i] < best:
                best = dist[i]
                node = i
        if node == -1:
            break
        visited.add(node)
        for to, weight in graph.get(node, []):
            if dist[node] + weight < dist[to]:
                dist[to] = dist[node] + weight
    answer = max(dist[1:])
    return -1 if answer == float('inf') else answer


class Solution:
    def networkDelayTime(self, times: list[list[int]], n: int, k: int) -> int:
        return solve(times, n, k)
