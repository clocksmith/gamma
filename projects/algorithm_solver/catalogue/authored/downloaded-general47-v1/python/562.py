"""562. Longest Line of Consecutive One in Matrix (Medium).

Specification: https://leetcode.com/problems/longest-line-of-consecutive-one-in-matrix/description/
"""


def solve(mat: list[list[int]]) -> int:
    rows, cols = len(mat), len(mat[0])
    horizontal = [[0] * cols for _ in range(rows)]
    vertical = [[0] * cols for _ in range(rows)]
    diagonal = [[0] * cols for _ in range(rows)]
    anti_diagonal = [[0] * cols for _ in range(rows)]
    best = 0
    for r in range(rows):
        for c in range(cols):
            if mat[r][c] == 1:
                horizontal[r][c] = (horizontal[r][c - 1] if c > 0 else 0) + 1
                vertical[r][c] = (vertical[r - 1][c] if r > 0 else 0) + 1
                diagonal[r][c] = (diagonal[r - 1][c - 1] if r > 0 and c > 0 else 0) + 1
                anti_diagonal[r][c] = (anti_diagonal[r - 1][c + 1] if r > 0 and c + 1 < cols else 0) + 1
                best = max(best, horizontal[r][c], vertical[r][c], diagonal[r][c], anti_diagonal[r][c])
    return best


class Solution:
    def longestLine(self, mat: list[list[int]]) -> int:
        return solve(mat)
