"""694. Number of Distinct Islands. Canonical translation-only coordinate signatures; preserve the grid."""

def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    seen, shapes = set(), set()
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack, cells = [(row, col)], []
            while stack:
                r, c = stack.pop()
                cells.append((r - row, c - col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            shapes.add(tuple(sorted(cells)))
    return len(shapes)


class Solution:
    def numDistinctIslands(self, grid: list[list[int]]) -> int:
        return solve(grid)
