"""1020. Number of Enclaves (Medium).

Specification: https://leetcode.com/problems/number-of-enclaves/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    remaining = [row[:] for row in grid]
    stack = []
    def enqueue(r, c):
        if remaining[r][c] == 1:
            remaining[r][c] = 0
            stack.append((r, c))
    for r in range(rows):
        enqueue(r, 0)
        enqueue(r, cols - 1)
    for c in range(cols):
        enqueue(0, c)
        enqueue(rows - 1, c)
    while stack:
        r, c = stack.pop()
        for a, b in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= a < rows and 0 <= b < cols:
                enqueue(a, b)
    return sum(sum(row) for row in remaining)

class Solution:
    def numEnclaves(self, grid: list[list[int]]) -> int:
        return solve(grid)
