"""794. Valid Tic-Tac-Toe State (Medium).

Specification: https://leetcode.com/problems/valid-tic-tac-toe-state/description/
"""


def _wins(board, player):
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
        if board[0][i] == player and board[1][i] == player and board[2][i] == player:
            return True
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False


def solve(board: list[str]) -> bool:
    x_count = 0
    o_count = 0
    for row in board:
        for ch in row:
            if ch == 'X':
                x_count += 1
            elif ch == 'O':
                o_count += 1
    if o_count > x_count or x_count - o_count > 1:
        return False
    x_wins = _wins(board, 'X')
    o_wins = _wins(board, 'O')
    if x_wins and o_wins:
        return False
    if x_wins and x_count != o_count + 1:
        return False
    if o_wins and x_count != o_count:
        return False
    return True


class Solution:
    def validTicTacToe(self, board: list[str]) -> bool:
        return solve(board)
