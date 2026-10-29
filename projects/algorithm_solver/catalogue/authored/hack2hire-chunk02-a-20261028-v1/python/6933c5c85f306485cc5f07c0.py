"""Hack2Hire 6933c5c85f306485cc5f07c0 (Maximum Island Perimeter); INFERRED spec; qualification unknown."""


def solve(grid):
    rows, cols = len(grid), len(grid[0])
    seen = [[False] * cols for _ in range(rows)]
    best = 0
    for r0 in range(rows):
        for c0 in range(cols):
            if grid[r0][c0] != '1' or seen[r0][c0]: continue
            seen[r0][c0] = True
            stack, perimeter = [(r0, c0)], 0
            while stack:
                r, c = stack.pop()
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] != '1': perimeter += 1
                    elif not seen[nr][nc]: seen[nr][nc] = True; stack.append((nr, nc))
            best = max(best, perimeter)
    return best


class Solution:
    def maxIslandPerimeter(self, grid):
        return solve(grid)
