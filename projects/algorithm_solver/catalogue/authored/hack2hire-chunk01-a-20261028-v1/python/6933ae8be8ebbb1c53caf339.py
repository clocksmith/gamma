"""Hack2Hire 6933ae8be8ebbb1c53caf339 (Count Islands and Water Boundary) over an INFERRED spec; qualification unknown."""


def solve(grid):
    rows, cols = len(grid), len(grid[0])
    seen = [[False] * cols for _ in range(rows)]
    result = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != '1' or seen[r][c]:
                continue
            seen[r][c] = True
            queue, area, boundary, head = [(r, c)], 0, 0, 0
            while head < len(queue):
                x, y = queue[head]
                head += 1
                area += 1
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < rows and 0 <= ny < cols:
                        if grid[nx][ny] == '0':
                            boundary += 1
                        elif not seen[nx][ny]:
                            seen[nx][ny] = True
                            queue.append((nx, ny))
            result.append([area, boundary])
    return result


class Solution:
    def islandStats(self, grid):
        return solve(grid)
