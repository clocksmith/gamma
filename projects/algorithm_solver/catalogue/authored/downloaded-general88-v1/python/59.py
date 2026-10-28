"""59. Spiral Matrix II (Medium).

Specification: https://leetcode.com/problems/spiral-matrix-ii/description/
"""


def solve(n: int) -> list[list[int]]:
    result = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    value = 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            result[top][c] = value
            value += 1
        top += 1
        for r in range(top, bottom + 1):
            result[r][right] = value
            value += 1
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                result[bottom][c] = value
                value += 1
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result[r][left] = value
                value += 1
            left += 1
    return result


class Solution:
    def generateMatrix(self, n: int) -> list[list[int]]:
        return solve(n)
