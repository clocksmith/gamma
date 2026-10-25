def cardinal_neighbors(row: int, column: int, rows: int, columns: int):
    for row_step, column_step in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        next_row = row + row_step
        next_column = column + column_step
        if 0 <= next_row < rows and 0 <= next_column < columns:
            yield next_row, next_column


class Solution:
    def exist(self, board: list[list[str]], word: str) -> bool:
        if not word:
            return True
        rows = len(board)
        columns = len(board[0]) if rows > 0 else 0
        if rows == 0 or columns == 0 or len(word) > rows * columns:
            return False
        visited = [[False] * columns for _ in range(rows)]
        for start_row in range(rows):
            for start_column in range(columns):
                stack = [(start_row, start_column, 0, False)]
                while stack:
                    row, column, offset, expanded = stack.pop()
                    if expanded:
                        visited[row][column] = False
                        continue
                    if visited[row][column] or board[row][column] != word[offset]:
                        continue
                    visited[row][column] = True
                    if offset + 1 == len(word):
                        return True
                    stack.append((row, column, offset, True))
                    for next_row, next_column in cardinal_neighbors(row, column, rows, columns):
                        if not visited[next_row][next_column]:
                            stack.append((next_row, next_column, offset + 1, False))
        return False
