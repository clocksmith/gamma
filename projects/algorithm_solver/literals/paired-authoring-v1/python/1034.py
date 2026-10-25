def cardinal_neighbors(row: int, column: int, rows: int, columns: int):
    for row_step, column_step in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        next_row = row + row_step
        next_column = column + column_step
        if 0 <= next_row < rows and 0 <= next_column < columns:
            yield next_row, next_column


class Solution:
    def colorBorder(self, grid: list[list[int]], row: int, col: int, color: int) -> list[list[int]]:
        rows = len(grid)
        columns = len(grid[0])
        original = grid[row][col]
        visited = [[False] * columns for _ in range(rows)]
        visited[row][col] = True
        queue = [(row, col)]
        border = []
        head = 0
        while head < len(queue):
            current_row, current_column = queue[head]
            head += 1
            on_border = current_row == 0 or current_row == rows - 1
            on_border = on_border or current_column == 0 or current_column == columns - 1
            for next_row, next_column in cardinal_neighbors(current_row, current_column, rows, columns):
                if grid[next_row][next_column] != original:
                    on_border = True
                elif not visited[next_row][next_column]:
                    visited[next_row][next_column] = True
                    queue.append((next_row, next_column))
            if on_border:
                border.append((current_row, current_column))
        for border_row, border_column in border:
            grid[border_row][border_column] = color
        return grid
