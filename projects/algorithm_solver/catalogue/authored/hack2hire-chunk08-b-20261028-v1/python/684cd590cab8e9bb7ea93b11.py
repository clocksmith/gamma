"""Hack2Hire 684cd590cab8e9bb7ea93b11 (Tic-Tac-Toe II) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class TicTacToe:
    def __init__(self, n, m, k):
        self.m = m
        self.k = k
        self.owner = {}
        self.run = [{}, {}, {}, {}]   # per direction: run length stored at both endpoints of each run

    def move(self, row, col, player):
        m, owner = self.m, self.owner
        owner[row * m + col] = player
        won = False
        for d, (dr, dc) in enumerate(_DIRECTIONS):
            run = self.run[d]
            before, after = row * m + col - (dr * m + dc), row * m + col + (dr * m + dc)
            left = run[before] if 0 <= col - dc < m and owner.get(before) == player else 0
            right = run[after] if 0 <= col + dc < m and owner.get(after) == player else 0
            total = left + right + 1
            run[(row - left * dr) * m + col - left * dc] = total
            run[(row + right * dr) * m + col + right * dc] = total
            if total >= self.k:
                won = True
        return player if won else 0


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TicTacToe' or len(argument_lists[0]) != 3:
        raise ValueError('exact initial constructor required')
    instance = TicTacToe(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'move':
            raise ValueError('unknown method')
        result.append(instance.move(*arguments))
    return result
