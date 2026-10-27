"""419. Battleships in a Board. Count each valid ship at its top-left endpoint; do not modify the board."""

def solve(board: list[list[str]]) -> int:
    return sum(board[r][c] == 'X'
               and (r == 0 or board[r - 1][c] != 'X')
               and (c == 0 or board[r][c - 1] != 'X')
               for r in range(len(board)) for c in range(len(board[0])))


class Solution:
    def countBattleships(self, board: list[list[str]]) -> int:
        return solve(board)
