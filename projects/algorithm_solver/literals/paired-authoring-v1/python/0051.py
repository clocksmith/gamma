class Solution:
    def solveNQueens(self, n: int) -> list[list[str]]:
        columns = [False] * n
        descending = [False] * (2 * n + 1)
        ascending = [False] * (2 * n + 1)
        placement = []
        boards = []

        def collect(row: int) -> None:
            if row == n:
                board = []
                for column in placement:
                    board.append("." * column + "Q" + "." * (n - column - 1))
                boards.append(board)
                return
            for column in range(n):
                down = row - column + n
                up = row + column
                if columns[column] or descending[down] or ascending[up]:
                    continue
                columns[column] = True
                descending[down] = True
                ascending[up] = True
                placement.append(column)
                collect(row + 1)
                placement.pop()
                columns[column] = False
                descending[down] = False
                ascending[up] = False

        collect(0)
        return boards
