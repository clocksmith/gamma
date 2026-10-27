"""289. Game of Life."""
def solve(board: list[list[int]]) -> None:
    rows, columns = len(board), len(board[0])
    for row in range(rows):
        for column in range(columns):
            live = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        nr, nc = row + dr, column + dc
                        if 0 <= nr < rows and 0 <= nc < columns:
                            live += board[nr][nc] & 1
            if board[row][column] & 1 and live in (2, 3) or not board[row][column] & 1 and live == 3:
                board[row][column] |= 2
    for row in range(rows):
        for column in range(columns):
            board[row][column] >>= 1

class Solution:
    def gameOfLife(self, board: list[list[int]]) -> None:
        solve(board)
