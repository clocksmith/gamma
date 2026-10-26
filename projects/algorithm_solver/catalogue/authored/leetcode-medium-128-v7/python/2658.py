"""2658. Maximum Number of Fish in a Grid: sum connected positive cells with an explicit stack and separate visitation state."""


def solve(grid: list[list[int]]) -> int:
    """O(r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    seen = [False] * (rows * columns)
    best = 0
    for row in range(rows):
        for column in range(columns):
            start = row * columns + column
            if seen[start] or grid[row][column] == 0:
                continue
            seen[start] = True
            stack = [(row, column)]
            total = 0
            while stack:
                current_row, current_column = stack.pop()
                total += grid[current_row][current_column]
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = current_row + dr, current_column + dc
                    if 0 <= nr < rows and 0 <= nc < columns:
                        index = nr * columns + nc
                        if not seen[index] and grid[nr][nc] > 0:
                            seen[index] = True
                            stack.append((nr, nc))
            best = max(best, total)
    return best


class Solution:
    def findMaxFish(self, grid: list[list[int]]) -> int:
        return solve(grid)
