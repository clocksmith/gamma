"""3643. Flip Square Submatrix Vertically (Easy).

Specification: https://leetcode.com/problems/flip-square-submatrix-vertically/description/
"""


def solve(grid: list[list[int]], x: int, y: int, k: int) -> list[list[int]]:
    """O(m * n + k * k) time, O(m * n) output space; preserve grid and every input row."""
    result = [row[:] for row in grid]
    for offset in range(k // 2):
        top = x + offset
        bottom = x + k - 1 - offset
        for column in range(y, y + k):
            result[top][column], result[bottom][column] = result[bottom][column], result[top][column]
    return result


class Solution:
    def reverseSubmatrix(self, grid: list[list[int]], x: int, y: int, k: int) -> list[list[int]]:
        return solve(grid, x, y, k)
