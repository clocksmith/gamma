"""3977. Minimum Time to Reach Target With Limited Power
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-time-to-reach-target-with-limited-power/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3977.Minimum%20Time%20to%20Reach%20Target%20With%20Limited%20Power/README_EN.md
Complexity: O(power*(n+m)) time, O(n*power + m) space.
Positive departure costs make remaining-power states acyclic even when graph nodes contain cycles. Target incurs no cost unless departed. Minimum time, then maximum remaining power. Inputs preserved.
"""

from __future__ import annotations

def solve(n, edges, power, cost, source, target):
    graph = [[] for _ in range(n)]
    for start, end, duration in edges:
        graph[start].append((end, duration))
    distance = [[float('inf')] * (power + 1) for _ in range(n)]
    distance[source][power] = 0
    for remaining in range(power, -1, -1):
        for node in range(n):
            current = distance[node][remaining]
            if current == float('inf') or remaining < cost[node]:
                continue
            following = remaining - cost[node]
            for neighbor, duration in graph[node]:
                distance[neighbor][following] = min(distance[neighbor][following], current + duration)
    best = min(distance[target])
    if best == float('inf'):
        return [-1, -1]
    reserve = max(remaining for remaining in range(power + 1) if distance[target][remaining] == best)
    return [best, reserve]


class Solution:
    def minTimeMaxPower(self, n, edges, power, cost, source, target):
        return solve(n, edges, power, cost, source, target)
