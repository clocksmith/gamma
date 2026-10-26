"""1559. Detect Cycles in 2D Grid: detect non-parent revisits in each equal-letter grid component."""


def solve(grid: list[list[str]]) -> bool:
    """O(r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    rows, cols = len(grid), len(grid[0])
    seen = [False] * (rows * cols)
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for start_row in range(rows):
        for start_col in range(cols):
            start = start_row * cols + start_col
            if seen[start]:
                continue
            seen[start] = True
            stack = [(start_row, start_col, -1)]
            while stack:
                row, col, parent = stack.pop()
                current = row * cols + col
                for dr, dc in directions:
                    next_row, next_col = row + dr, col + dc
                    if not (0 <= next_row < rows and 0 <= next_col < cols):
                        continue
                    following = next_row * cols + next_col
                    if following == parent or grid[next_row][next_col] != grid[row][col]:
                        continue
                    if seen[following]:
                        return True
                    seen[following] = True
                    stack.append((next_row, next_col, current))
    return False


class Solution:
    def containsCycle(self, grid: list[list[str]]) -> bool:
        return solve(grid)
