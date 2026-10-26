"""2352. Equal Row and Column Pairs: count full row signatures and match each complete column against them."""
from collections import Counter


def solve(grid: list[list[int]]) -> int:
    """O(n^2) expected time and O(n^2) auxiliary space on the bounded integer domain; inputs are read-only."""
    rows = Counter(tuple(row) for row in grid)
    answer = 0
    for column in range(len(grid)):
        signature = tuple(grid[row][column] for row in range(len(grid)))
        answer += rows.get(signature, 0)
    return answer


class Solution:
    def equalPairs(self, grid: list[list[int]]) -> int:
        return solve(grid)
