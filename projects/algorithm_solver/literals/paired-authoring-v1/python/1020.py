def cardinal_neighbors(row: int, column: int, rows: int, columns: int):
    for row_step, column_step in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        next_row = row + row_step
        next_column = column + column_step
        if 0 <= next_row < rows and 0 <= next_column < columns:
            yield next_row, next_column


class Solution:
    def numEnclaves(self, grid: list[list[int]]) -> int:
        rows = len(grid)
        columns = len(grid[0]) if rows > 0 else 0
        if rows == 0 or columns == 0:
            return 0
        visited = [[False] * columns for _ in range(rows)]
        queue = []
        for row in range(rows):
            for column in range(columns):
                if row == 0 or row == rows - 1 or column == 0 or column == columns - 1:
                    if grid[row][column] == 1:
                        visited[row][column] = True
                        grid[row][column] = 0
                        queue.append((row, column))
        head = 0
        while head < len(queue):
            row, column = queue[head]
            head += 1
            for next_row, next_column in cardinal_neighbors(row, column, rows, columns):
                if grid[next_row][next_column] == 1 and not visited[next_row][next_column]:
                    visited[next_row][next_column] = True
                    grid[next_row][next_column] = 0
                    queue.append((next_row, next_column))
        count = 0
        for row in range(rows):
            for column in range(columns):
                if grid[row][column] == 1 and not visited[row][column]:
                    count += 1
        return count
