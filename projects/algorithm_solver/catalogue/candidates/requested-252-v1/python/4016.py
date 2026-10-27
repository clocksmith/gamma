"""4016. Maximum Area of Two Non-Overlapping Square Submatrices
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-area-of-two-non-overlapping-square-submatrices/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4016.Maximum%20Area%20of%20Two%20Non-Overlapping%20Square%20Submatrices/README_EN.md
Complexity: O(m*n) time, O(m+n) auxiliary space.
Any two nonoverlapping axis-aligned squares admit a horizontal or vertical separating cut. Bidirectional square DP supplies maxima on both sides; smaller side gives equal-sized squares. Inputs preserved.
"""

from __future__ import annotations

def solve(mat):
    m, n = len(mat), len(mat[0])
    row_end, col_end = [0] * m, [0] * n
    row_start, col_start = [0] * m, [0] * n
    previous = [0] * (n + 1)
    for r in range(m):
        current = [0] * (n + 1)
        for c in range(n):
            if mat[r][c]:
                size = 1 + min(previous[c], previous[c + 1], current[c])
                current[c + 1] = size
                row_end[r] = max(row_end[r], size)
                col_end[c] = max(col_end[c], size)
        previous = current
    previous = [0] * (n + 1)
    for r in range(m - 1, -1, -1):
        current = [0] * (n + 1)
        for c in range(n - 1, -1, -1):
            if mat[r][c]:
                size = 1 + min(previous[c], previous[c + 1], current[c + 1])
                current[c] = size
                row_start[r] = max(row_start[r], size)
                col_start[c] = max(col_start[c], size)
        previous = current
    answer = 0
    for ends, starts in ((row_end, row_start), (col_end, col_start)):
        for i in range(1, len(ends)):
            ends[i] = max(ends[i], ends[i - 1])
        for i in range(len(starts) - 2, -1, -1):
            starts[i] = max(starts[i], starts[i + 1])
        for i in range(len(ends) - 1):
            answer = max(answer, min(ends[i], starts[i + 1]) ** 2)
    return answer


class Solution:
    def maxArea(self, mat):
        return solve(mat)
