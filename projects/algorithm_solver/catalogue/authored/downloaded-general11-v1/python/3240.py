"""3240. Minimum Number of Flips to Make Binary Grid Palindromic II (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-flips-to-make-binary-grid-palindromic-ii/description/
"""


def solve(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    ans = 0
    middle_ones = 0
    mismatched = 0
    for i in range(m // 2):
        for j in range(n // 2):
            ones = (grid[i][j] + grid[i][n - 1 - j]
                    + grid[m - 1 - i][j] + grid[m - 1 - i][n - 1 - j])
            ans += min(ones, 4 - ones)
    if m % 2 == 1:
        mid = m // 2
        for j in range(n // 2):
            a, b = grid[mid][j], grid[mid][n - 1 - j]
            mismatched += a ^ b
            middle_ones += a + b
    if n % 2 == 1:
        mid = n // 2
        for i in range(m // 2):
            a, b = grid[i][mid], grid[m - 1 - i][mid]
            mismatched += a ^ b
            middle_ones += a + b
    if mismatched == 0:
        if middle_ones % 4 == 2:
            ans += 2
    else:
        ans += mismatched
    if m % 2 == 1 and n % 2 == 1:
        ans += grid[m // 2][n // 2]
    return ans


class Solution:
    def minFlips(self, grid):
        return solve(grid)
