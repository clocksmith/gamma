"""2711. Difference of Number of Distinct Values on Diagonals (Medium).

Specification: https://leetcode.com/problems/difference-of-number-of-distinct-values-on-diagonals/description/
"""


def solve(grid: list[list[int]]) -> list[list[int]]:
    m, n = len(grid), len(grid[0])
    answer = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            top_left = set()
            i, j = r - 1, c - 1
            while i >= 0 and j >= 0:
                top_left.add(grid[i][j])
                i -= 1
                j -= 1
            bottom_right = set()
            i, j = r + 1, c + 1
            while i < m and j < n:
                bottom_right.add(grid[i][j])
                i += 1
                j += 1
            answer[r][c] = abs(len(top_left) - len(bottom_right))
    return answer


class Solution:
    def differenceOfDistinctValues(self, grid: list[list[int]]) -> list[list[int]]:
        return solve(grid)
