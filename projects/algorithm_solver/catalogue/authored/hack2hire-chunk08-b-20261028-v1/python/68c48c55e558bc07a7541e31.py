"""Hack2Hire 68c48c55e558bc07a7541e31 (Snake Game) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque

_STEP = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


class SnakeGame:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.body = deque([0])
        self.occupied = {0}
        self.row = 0
        self.col = 0
        self.moves = 0
        self.alive = True

    def move(self, direction):
        if not self.alive:
            return False
        self.moves += 1
        dr, dc = _STEP[direction]
        r, c = self.row + dr, self.col + dc
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            self.alive = False
            return False
        if self.moves % 5 != 0:
            self.occupied.discard(self.body.popleft())
        cell = r * self.cols + c
        if cell in self.occupied:
            self.alive = False
            return False
        self.body.append(cell)
        self.occupied.add(cell)
        self.row, self.col = r, c
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SnakeGame' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = SnakeGame(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'move':
            raise ValueError('unknown method')
        result.append(instance.move(*arguments))
    return result
