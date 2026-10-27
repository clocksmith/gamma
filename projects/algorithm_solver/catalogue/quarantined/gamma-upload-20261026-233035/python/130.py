"""130. Surrounded Regions."""
from collections import deque

def solve(board: list[list[str]]) -> None:
    if not board or not board[0]:
        return
    rows, columns = len(board), len(board[0])
    queue = deque()
    for row in range(rows):
        for column in (0, columns - 1):
            if board[row][column] == 'O':
                queue.append((row, column))
                board[row][column] = '#'
    for column in range(columns):
        for row in (0, rows - 1):
            if board[row][column] == 'O':
                queue.append((row, column))
                board[row][column] = '#'
    while queue:
        row, column = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and board[nr][nc] == 'O':
                board[nr][nc] = '#'
                queue.append((nr, nc))
    for row in range(rows):
        for column in range(columns):
            board[row][column] = 'O' if board[row][column] == '#' else 'X'

class Solution:
    def solve(self, board: list[list[str]]) -> None:
        solve(board)
