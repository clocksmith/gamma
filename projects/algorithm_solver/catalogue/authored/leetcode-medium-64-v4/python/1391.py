"""1391. Check if There is a Valid Path in a Grid: traverse only street openings whose neighboring tiles connect back."""


def solve(grid: list[list[int]]) -> bool:
    """O(r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    openings = ((), (1, 3), (0, 2), (2, 3), (1, 2), (0, 3), (0, 1))
    directions = ((-1, 0), (0, 1), (1, 0), (0, -1))
    rows, cols = len(grid), len(grid[0])
    seen = [False] * (rows * cols)
    seen[0] = True
    stack = [(0, 0)]
    while stack:
        row, col = stack.pop()
        if row == rows - 1 and col == cols - 1:
            return True
        for direction in openings[grid[row][col]]:
            dr, dc = directions[direction]
            next_row, next_col = row + dr, col + dc
            if not (0 <= next_row < rows and 0 <= next_col < cols):
                continue
            index = next_row * cols + next_col
            if not seen[index] and (direction + 2) % 4 in openings[grid[next_row][next_col]]:
                seen[index] = True
                stack.append((next_row, next_col))
    return False


class Solution:
    def hasValidPath(self, grid: list[list[int]]) -> bool:
        return solve(grid)
