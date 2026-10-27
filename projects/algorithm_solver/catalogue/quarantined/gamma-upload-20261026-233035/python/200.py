"""200. Number of Islands."""
def solve(grid: list[list[str]]) -> int:
    rows, columns = len(grid), len(grid[0])
    count = 0
    for row in range(rows):
        for column in range(columns):
            if grid[row][column] != '1':
                continue
            count += 1
            stack = [(row, column)]
            grid[row][column] = '0'
            while stack:
                current_row, current_column = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = current_row + dr, current_column + dc
                    if 0 <= nr < rows and 0 <= nc < columns and grid[nr][nc] == '1':
                        grid[nr][nc] = '0'
                        stack.append((nr, nc))
    return count

class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        return solve(grid)
