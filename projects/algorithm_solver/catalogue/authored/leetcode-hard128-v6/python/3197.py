"""3197. Find the Minimum Area to Cover All Ones II.

Enumerate the six possible three-rectangle split layouts; O(h*w*(h^2+w^2+h*w)) time, O(1) auxiliary space. Inputs are preserved.
"""

def solve(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])

    def area(top, bottom, left, right):
        min_row, max_row, min_col, max_col = h, -1, w, -1
        for row in range(top, bottom):
            for col in range(left, right):
                if grid[row][col]:
                    min_row, max_row = min(min_row, row), max(max_row, row)
                    min_col, max_col = min(min_col, col), max(max_col, col)
        return float('inf') if max_row < 0 else (max_row - min_row + 1) * (max_col - min_col + 1)

    answer = float('inf')
    for first in range(1, h):
        for second in range(first + 1, h):
            answer = min(answer, area(0, first, 0, w) + area(first, second, 0, w) + area(second, h, 0, w))
    for first in range(1, w):
        for second in range(first + 1, w):
            answer = min(answer, area(0, h, 0, first) + area(0, h, first, second) + area(0, h, second, w))
    for row in range(1, h):
        for col in range(1, w):
            answer = min(answer,
                         area(0, row, 0, w) + area(row, h, 0, col) + area(row, h, col, w),
                         area(row, h, 0, w) + area(0, row, 0, col) + area(0, row, col, w),
                         area(0, h, 0, col) + area(0, row, col, w) + area(row, h, col, w),
                         area(0, h, col, w) + area(0, row, 0, col) + area(row, h, 0, col))
    return answer


class Solution:
    def minimumSum(self, grid: list[list[int]]) -> int:
        return solve(grid)
