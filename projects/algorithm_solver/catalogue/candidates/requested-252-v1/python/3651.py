"""3651. Minimum Cost Path with Teleportations
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-cost-path-with-teleportations/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3651.Minimum%20Cost%20Path%20with%20Teleportations/README_EN.md
Complexity: O(mn log(mn) + k mn) time; O(mn) space.
Grid is preserved; start-cell cost is zero; equal-value teleport groups are handled together.
"""

from __future__ import annotations

def solve(grid, k):
    rows, columns = len(grid), len(grid[0])
    values = [value for row in grid for value in row]
    order = sorted(range(len(values)), key=values.__getitem__, reverse=True)
    costs = [float('inf')] * len(values)
    costs[0] = 0
    def relax(costs):
        for row in range(rows):
            for column in range(columns):
                index = row * columns + column
                if row:
                    costs[index] = min(costs[index], costs[index - columns] + values[index])
                if column:
                    costs[index] = min(costs[index], costs[index - 1] + values[index])
    relax(costs)
    answer = costs[-1]
    for _ in range(k):
        next_costs = [float('inf')] * len(values)
        best = float('inf')
        start = 0
        while start < len(order):
            end = start
            while end < len(order) and values[order[end]] == values[order[start]]:
                best = min(best, costs[order[end]])
                end += 1
            for offset in range(start, end):
                next_costs[order[offset]] = best
            start = end
        relax(next_costs)
        costs = next_costs
        answer = min(answer, costs[-1])
    return answer


class Solution:
    def minCost(self, grid, k):
        return solve(grid, k)
