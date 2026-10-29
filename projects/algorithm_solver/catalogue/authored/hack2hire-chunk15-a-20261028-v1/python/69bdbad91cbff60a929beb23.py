"""Hack2Hire 69bdbad91cbff60a929beb23 (Design Connect Four II, variant 1 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class ConnectFourBoard:
    def __init__(self, rows, cols):
        self.rows = rows
        self.grid = [['0'] * cols for _ in range(rows)]
        self.height = [0] * cols

    def drop(self, color, col):
        if self.height[col] < self.rows:
            self.grid[self.rows - 1 - self.height[col]][col] = color
            self.height[col] += 1
        return [row[:] for row in self.grid]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ConnectFourBoard' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = ConnectFourBoard(*argument_lists[0])
    allowed = {'drop'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
