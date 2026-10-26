"""1536. Minimum Swaps to Arrange a Binary Grid: move the nearest row with enough trailing zeros into each position."""


def solve(grid: list[list[int]]) -> int:
    """O(n^2) time and O(n) auxiliary space; inputs are read-only."""
    size = len(grid)
    trailing = []
    for row in grid:
        count = 0
        for col in range(size - 1, -1, -1):
            if row[col]:
                break
            count += 1
        trailing.append(count)
    swaps = 0
    for row in range(size):
        needed = size - row - 1
        chosen = row
        while chosen < size and trailing[chosen] < needed:
            chosen += 1
        if chosen == size:
            return -1
        swaps += chosen - row
        value = trailing[chosen]
        while chosen > row:
            trailing[chosen] = trailing[chosen - 1]
            chosen -= 1
        trailing[row] = value
    return swaps


class Solution:
    def minSwaps(self, grid: list[list[int]]) -> int:
        return solve(grid)
