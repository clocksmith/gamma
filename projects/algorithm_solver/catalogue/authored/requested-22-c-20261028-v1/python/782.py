"""Original frontend 782 variant; qualification not qualified."""

def solve(board):
    n = len(board)
    for i in range(n):
        for j in range(n):
            if board[0][0] ^ board[i][0] ^ board[0][j] ^ board[i][j]:
                return -1
    row_ones = sum(board[0])
    col_ones = sum(board[i][0] for i in range(n))
    if not n // 2 <= row_ones <= (n + 1) // 2 or not n // 2 <= col_ones <= (n + 1) // 2:
        return -1
    row_misplaced = sum(1 for j in range(n) if board[0][j] == j % 2)
    col_misplaced = sum(1 for i in range(n) if board[i][0] == i % 2)
    if n % 2:
        if row_misplaced % 2:
            row_misplaced = n - row_misplaced
        if col_misplaced % 2:
            col_misplaced = n - col_misplaced
    else:
        row_misplaced = min(row_misplaced, n - row_misplaced)
        col_misplaced = min(col_misplaced, n - col_misplaced)
    return (row_misplaced + col_misplaced) // 2


class Solution:
    def movesToChessboard(self, board):
        return solve(board)
