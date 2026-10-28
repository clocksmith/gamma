"""48. Rotate Image (Medium).

Specification: https://leetcode.com/problems/rotate-image/description/
"""


def solve(matrix: list[list[int]]) -> list[list[int]]:
    n = len(matrix)
    result = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            result[c][n - 1 - r] = matrix[r][c]
    return result


class Solution:
    def rotate(self, matrix: list[list[int]]) -> list[list[int]]:
        return solve(matrix)
