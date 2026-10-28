"""Original iterative variant; preserves the caller's binary grid."""


def solve(grid):
    rows, columns = len(grid), len(grid[0])
    visited = bytearray(rows * columns)
    largest = 0
    for row in range(rows):
        for column in range(columns):
            start = row * columns + column
            if not grid[row][column] or visited[start]:
                continue
            visited[start] = 1
            pending = [start]
            area = 0
            while pending:
                index = pending.pop()
                r, c = divmod(index, columns)
                area += 1
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < rows and 0 <= nc < columns:
                        neighbor = nr * columns + nc
                        if grid[nr][nc] and not visited[neighbor]:
                            visited[neighbor] = 1
                            pending.append(neighbor)
            if area > largest:
                largest = area
    return largest


class Solution:
    def maxAreaOfIsland(self, grid):
        return solve(grid)
