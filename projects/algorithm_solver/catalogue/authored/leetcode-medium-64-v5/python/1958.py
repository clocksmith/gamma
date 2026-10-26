"""1958. Check if Move is Legal: look for an opposite-color run closed by the chosen color in any direction."""


def solve(board: list[list[str]], rMove: int, cMove: int, color: str) -> bool:
    """O(1) time and O(1) auxiliary space on the fixed 8-by-8 board; inputs are read-only."""
    opponent = 'W' if color == 'B' else 'B'
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            row, column = rMove + dr, cMove + dc
            crossed = 0
            while 0 <= row < 8 and 0 <= column < 8 and board[row][column] == opponent:
                crossed += 1
                row += dr
                column += dc
            if crossed > 0 and 0 <= row < 8 and 0 <= column < 8 and board[row][column] == color:
                return True
    return False


class Solution:
    def checkMove(self, board: list[list[str]], rMove: int, cMove: int, color: str) -> bool:
        return solve(board, rMove, cMove, color)
