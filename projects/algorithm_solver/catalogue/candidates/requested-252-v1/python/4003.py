"""4003. Minimum Cost Path with Alternating Directions III
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-cost-path-with-alternating-directions-iii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4003.Minimum%20Cost%20Path%20with%20Alternating%20Directions%20III/README_EN.md
Complexity: O(m*n*log(m*n)) time, O(m*n) space.
Dijkstra state includes next-action parity. Waiting and moves both flip parity; violations charge the departure cell. Includes starting entrance cost. Inputs preserved.
"""

from __future__ import annotations
from heapq import heappop, heappush

def solve(m, n, penalty):
    distance = [float('inf')] * (2 * m * n)
    distance[1] = 1
    queue = [(1, 1)]
    while queue:
        total, state = heappop(queue)
        if total != distance[state]:
            continue
        cell, odd = divmod(state, 2)
        if cell == m * n - 1:
            return total
        row, col = divmod(cell, n)
        surcharge = penalty[row][col]
        neighbors = [(cell, surcharge)]
        for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            r, c = row + dr, col + dc
            if 0 <= r < m and 0 <= c < n:
                forward = dr + dc > 0
                extra = 0 if forward == bool(odd) else surcharge
                neighbors.append((r * n + c, (r + 1) * (c + 1) + extra))
        for neighbor, cost in neighbors:
            following = 2 * neighbor + (odd ^ 1)
            candidate = total + cost
            if candidate < distance[following]:
                distance[following] = candidate
                heappush(queue, (candidate, following))
    return -1


class Solution:
    def minCost(self, m, n, penalty):
        return solve(m, n, penalty)
