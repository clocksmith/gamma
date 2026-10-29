"""Original frontend 296 variant; qualification unknown."""


def solve(grid) -> int:
    rows = [r for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 1]
    cols = [c for c in range(len(grid[0])) for r in range(len(grid)) if grid[r][c] == 1]

    def dist_1d(arr) -> int:
        l, r = 0, len(arr) - 1
        s = 0
        while l < r:
            s += arr[r] - arr[l]
            l += 1
            r -= 1
        return s

    return dist_1d(rows) + dist_1d(cols)


minTotalDistance = solve


class Solution:
    def minTotalDistance(self, grid) -> int:
        return solve(grid)
