"""3989. Maximum Consistent Columns in a Grid
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-consistent-columns-in-a-grid/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3989.Maximum%20Consistent%20Columns%20in%20a%20Grid/README_EN.md
Complexity: O(m*n^2) time, O(n) space.
Longest path in the column-order DAG, with all-row compatibility on every transition. Inputs preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(grid, limit):
    n = len(grid[0])
    best = [1] * n
    for right in range(n):
        for left in range(right):
            if best[left] >= best[right] and all(abs(row[right] - row[left]) <= limit for row in grid):
                best[right] = best[left] + 1
    return max(best)
