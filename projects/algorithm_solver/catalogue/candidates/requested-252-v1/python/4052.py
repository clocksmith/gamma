"""4052. Cyclically Shift Rows and Columns
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/cyclically-shift-rows-and-columns/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4052.Cyclically%20Shift%20Rows%20and%20Columns/README_EN.md
Complexity: O(n^2) time and output space.
Apply column displacement using the already-shifted column index. All inputs preserved.
"""

from __future__ import annotations

def solve(n, grid, rowShift, colShift):
    answer = [[0]*n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            shifted_col = (col-rowShift[row]) % n
            shifted_row = (row-colShift[shifted_col]) % n
            answer[shifted_row][shifted_col] = grid[row][col]
    return answer


class Solution:
    def cyclicShift(self, n, grid, rowShift, colShift):
        return solve(n, grid, rowShift, colShift)
