"""Hack2Hire 68b93d5483188776facc8ff6 (Design Connect Four, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

ROWS, COLUMNS = 6, 7


class ConnectFour:
    def __init__(self):
        self._board = [[None] * COLUMNS for _ in range(ROWS)]  # row 0 is the bottom
        self._heights = [0] * COLUMNS
        self._turn = 'A'
        self._moves = 0
        self._over = False

    def _run(self, row, column, d_row, d_column, player):
        count = 0
        row, column = row + d_row, column + d_column
        while 0 <= row < ROWS and 0 <= column < COLUMNS and self._board[row][column] == player:
            count += 1
            row, column = row + d_row, column + d_column
        return count

    def play(self, column):
        if self._over or not 0 <= column < COLUMNS or self._heights[column] == ROWS:
            return 'INVALID'
        player, row = self._turn, self._heights[column]
        self._board[row][column] = player
        self._heights[column] += 1
        self._moves += 1
        self._turn = 'B' if player == 'A' else 'A'
        for d_row, d_column in ((0, 1), (1, 0), (1, 1), (1, -1)):
            if 1 + self._run(row, column, d_row, d_column, player) + self._run(row, column, -d_row, -d_column, player) >= 4:
                self._over = True
                return player + '_WINS'
        if self._moves == ROWS * COLUMNS:
            self._over = True
            return 'DRAW'
        return 'ONGOING'


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ConnectFour':
        raise ValueError('exact initial constructor required')
    instance = ConnectFour(*argument_lists[0])
    allowed = ['play']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
