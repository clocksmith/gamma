"""3276. Select Cells in Grid With Maximum Score: process each value once with a used-row subset state."""


def solve(grid: list[list[int]]) -> int:
    """O(S + V*R*2^R) time and O(V + 2^R) auxiliary space. Inputs are preserved."""
    rows_by_value = {}
    for row, values in enumerate(grid):
        for value in values:
            rows_by_value[value] = rows_by_value.get(value, 0) | (1 << row)
    size = 1 << len(grid)
    best = [-1] * size
    best[0] = 0
    for value, available_rows in rows_by_value.items():
        following = best.copy()
        for mask, score in enumerate(best):
            if score < 0:
                continue
            available = available_rows & ~mask
            while available:
                bit = available & -available
                available -= bit
                following[mask | bit] = max(following[mask | bit], score + value)
        best = following
    return max(best)


class Solution:
    def maxScore(self, grid: list[list[int]]) -> int:
        return solve(grid)
