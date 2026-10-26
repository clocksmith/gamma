"""1568. Minimum Number of Days to Disconnect Island: component counting under one omitted land cell; O((rows*columns)^2) time and O(rows*columns) space."""


def solve(grid: list[list[int]]) -> int:
    rows, columns = len(grid), len(grid[0])
    land = [row * columns + column for row in range(rows) for column in range(columns) if grid[row][column]]

    def components(omitted: int = -1) -> int:
        seen = set()
        count = 0
        for start in land:
            if start == omitted or start in seen:
                continue
            count += 1
            if count > 1:
                return count
            seen.add(start)
            stack = [start]
            while stack:
                row, column = divmod(stack.pop(), columns)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, column + dc
                    if not (0 <= nr < rows and 0 <= nc < columns) or grid[nr][nc] == 0:
                        continue
                    neighbor = nr * columns + nc
                    if neighbor != omitted and neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
        return count

    if components() != 1:
        return 0
    for cell in land:
        if components(cell) != 1:
            return 1
    return 2


class Solution:
    def minDays(self, grid: list[list[int]]) -> int:
        return solve(grid)
