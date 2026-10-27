"""348. Design Tic-Tac-Toe."""
class TicTacToe:
    def __init__(self, n: int):
        self.size = n
        self.rows = [0] * n
        self.columns = [0] * n
        self.diagonal = 0
        self.anti_diagonal = 0

    def move(self, row: int, col: int, player: int) -> int:
        value = 1 if player == 1 else -1
        self.rows[row] += value
        self.columns[col] += value
        if row == col:
            self.diagonal += value
        if row + col == self.size - 1:
            self.anti_diagonal += value
        if (abs(self.rows[row]) == self.size or abs(self.columns[col]) == self.size
                or abs(self.diagonal) == self.size or abs(self.anti_diagonal) == self.size):
            return player
        return 0

def solve(n: int, moves: list[list[int]]) -> list[int]:
    game = TicTacToe(n)
    return [game.move(*move) for move in moves]
