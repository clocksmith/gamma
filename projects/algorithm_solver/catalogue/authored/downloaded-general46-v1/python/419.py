"""419. Battleships in a Board (Medium).

Specification: https://leetcode.com/problems/battleships-in-a-board/description/
"""


def solve(board: list[list[str]]) -> int:
    count = 0
    for r in range(len(board)):
        for c in range(len(board[0])):
            if board[r][c] != 'X':
                continue
            if r > 0 and board[r - 1][c] == 'X':
                continue
            if c > 0 and board[r][c - 1] == 'X':
                continue
            count += 1
    return count


class Solution:
    def countBattleships(self, board: list[list[str]]) -> int:
        return solve(board)
