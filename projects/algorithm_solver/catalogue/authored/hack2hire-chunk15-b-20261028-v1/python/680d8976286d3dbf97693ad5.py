"""Hack2Hire 680d8976286d3dbf97693ad5 (Four-in-a-row Game) over an INFERRED spec; qualification unknown."""


def solve(board, move, player):
    x, y = move
    rows, cols = len(board), len(board[0])
    for dx, dy in ((0, 1), (1, 0), (1, 1), (1, -1)):
        run = 1
        for sign in (1, -1):
            a, b = x + sign * dx, y + sign * dy
            steps = 0
            while steps < 3 and 0 <= a < rows and 0 <= b < cols and board[a][b] == player:
                run += 1
                steps += 1
                a += sign * dx
                b += sign * dy
        if run >= 4:
            return True
    return False


class Solution:
    def isWinningMove(self, board, move, player):
        return solve(board, move, player)
