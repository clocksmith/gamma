"""1275. Find Winner on a Tic Tac Toe Game (Easy).

Specification: https://leetcode.com/problems/find-winner-on-a-tic-tac-toe-game/description/
"""


def solve(moves: list[list[int]]) -> str:
    """O(len(moves)) time, O(1) space on the 3-by-3 board; preserve moves."""
    rows = [0, 0, 0]
    columns = [0, 0, 0]
    main_diagonal = 0
    other_diagonal = 0
    for turn, (row, column) in enumerate(moves):
        mark = 1 if turn % 2 == 0 else -1
        rows[row] += mark
        columns[column] += mark
        if row == column:
            main_diagonal += mark
        if row + column == 2:
            other_diagonal += mark
        if (abs(rows[row]) == 3 or abs(columns[column]) == 3
                or abs(main_diagonal) == 3 or abs(other_diagonal) == 3):
            return 'A' if mark == 1 else 'B'
    return 'Draw' if len(moves) == 9 else 'Pending'


class Solution:
    def tictactoe(self, moves: list[list[int]]) -> str:
        return solve(moves)
