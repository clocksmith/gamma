"""Original frontend 741 variant; qualification unknown."""

def solve(grid):
    n = len(grid)
    unreachable = -1
    best = [[unreachable] * n for _ in range(n)]
    best[0][0] = grid[0][0]
    for step in range(1, 2 * n - 1):
        current = [[unreachable] * n for _ in range(n)]
        first = max(0, step - n + 1)
        last = min(n - 1, step)
        for row1 in range(first, last + 1):
            cell1 = grid[row1][step - row1]
            if cell1 == -1:
                continue
            for row2 in range(row1, last + 1):
                cell2 = grid[row2][step - row2]
                if cell2 == -1:
                    continue
                previous = best[row1][row2]
                if row1 and best[row1 - 1][row2] > previous:
                    previous = best[row1 - 1][row2]
                if row2 > row1 and best[row1][row2 - 1] > previous:
                    previous = best[row1][row2 - 1]
                if row1 and best[row1 - 1][row2 - 1] > previous:
                    previous = best[row1 - 1][row2 - 1]
                if previous == unreachable:
                    continue
                current[row1][row2] = previous + cell1 + (cell2 if row2 != row1 else 0)
        best = current
    return max(0, best[n - 1][n - 1])


class Solution:
    def cherryPickup(self, grid):
        return solve(grid)
