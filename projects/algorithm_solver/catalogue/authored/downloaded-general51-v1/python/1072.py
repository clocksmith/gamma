"""1072. Flip Columns For Maximum Number of Equal Rows (Medium).

Specification: https://leetcode.com/problems/flip-columns-for-maximum-number-of-equal-rows/description/
"""


def solve(matrix: list[list[int]]) -> int:
    counts = {}
    for row in matrix:
        pattern = "".join(str(v) for v in row) if row[0] == 0 else "".join(str(1 - v) for v in row)
        counts[pattern] = counts.get(pattern, 0) + 1
    best = 0
    for count in counts.values():
        best = max(best, count)
    return best


class Solution:
    def maxEqualRowsAfterFlips(self, matrix: list[list[int]]) -> int:
        return solve(matrix)
