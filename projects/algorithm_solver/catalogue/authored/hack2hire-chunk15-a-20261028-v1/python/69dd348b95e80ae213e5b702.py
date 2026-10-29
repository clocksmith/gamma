"""Hack2Hire 69dd348b95e80ae213e5b702 (Design Connect Four II, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class ConnectFourBoard:
    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.grid = [['0'] * cols for _ in range(rows)]
        self.height = [0] * cols
        self.winner = '0'

    def _run(self, r, c, dr, dc, color):
        length = 0
        r, c = r + dr, c + dc
        while 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == color:
            length += 1
            r, c = r + dr, c + dc
        return length

    def drop(self, color, col):
        if self.height[col] < self.rows:
            r = self.rows - 1 - self.height[col]
            self.grid[r][col] = color
            self.height[col] += 1
            if self.winner == '0':
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    if 1 + self._run(r, col, dr, dc, color) + self._run(r, col, -dr, -dc, color) >= 4:
                        self.winner = color
                        break
        return [row[:] for row in self.grid]

    def getWinner(self):
        return self.winner


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ConnectFourBoard' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = ConnectFourBoard(*argument_lists[0])
    allowed = {'drop', 'getWinner'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
