"""2850. Minimum Moves to Spread Stones Over Grid: assign each surplus stone to an empty cell with subset dynamic programming."""


def solve(grid: list[list[int]]) -> int:
    """O(z * 2^z) time and O(2^z) auxiliary space, where z is the number of empty cells; inputs are read-only."""
    surplus = []
    empty = []
    for row in range(3):
        for column in range(3):
            if grid[row][column] == 0:
                empty.append((row, column))
            else:
                surplus.extend([(row, column)] * (grid[row][column] - 1))
    size = len(empty)
    best = [float('inf')] * (1 << size)
    best[0] = 0
    for mask in range((1 << size) - 1):
        assigned = mask.bit_count()
        row, column = surplus[assigned]
        for index, (target_row, target_column) in enumerate(empty):
            bit = 1 << index
            if mask & bit == 0:
                target = mask | bit
                distance = abs(row - target_row) + abs(column - target_column)
                best[target] = min(best[target], best[mask] + distance)
    return int(best[-1])


class Solution:
    def minimumMoves(self, grid: list[list[int]]) -> int:
        return solve(grid)
