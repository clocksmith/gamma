"""3924. Minimum Threshold Path With Limited Heavy Edges
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-threshold-path-with-limited-heavy-edges/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3924.Minimum%20Threshold%20Path%20With%20Limited%20Heavy%20Edges/README_EN.md
Complexity: O((n+m) log(m+1)) time, O(n+m) space.
Threshold domain is nonnegative as illustrated by source==target returning 0. 0-1 BFS counts heavy edges. Native name pending.
"""

from __future__ import annotations
from collections import deque

def solve(n, edges, source, target, k):
    graph = [[] for _ in range(n)]
    for first, second, weight in edges:
        graph[first].append((second, weight))
        graph[second].append((first, weight))
    thresholds = sorted({0} | {edge[2] for edge in edges})
    def feasible(threshold):
        distances = [n + 1] * n
        distances[source] = 0
        queue = deque([(source, 0)])
        while queue:
            node, distance = queue.popleft()
            if distance != distances[node]:
                continue
            if node == target:
                return True
            for neighbor, weight in graph[node]:
                heavy = int(weight > threshold)
                updated = distance + heavy
                if updated <= k and updated < distances[neighbor]:
                    distances[neighbor] = updated
                    if heavy:
                        queue.append((neighbor, updated))
                    else:
                        queue.appendleft((neighbor, updated))
        return False
    if not feasible(thresholds[-1]):
        return -1
    left, right = 0, len(thresholds) - 1
    while left < right:
        middle = (left + right) // 2
        if feasible(thresholds[middle]):
            right = middle
        else:
            left = middle + 1
    return thresholds[left]
