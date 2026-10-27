"""497. Random Point in Non-overlapping Rectangles."""

from bisect import bisect_right
from random import randrange


class Solution:
    """Sample uniformly from integer lattice points, including rectangle boundaries."""
    def __init__(self, rects: list[list[int]]):
        self.rects = [rectangle[:] for rectangle in rects]
        self.prefix = []
        total = 0
        for x1, y1, x2, y2 in self.rects:
            total += (x2 - x1 + 1) * (y2 - y1 + 1)
            self.prefix.append(total)

    def pick(self) -> list[int]:
        ticket = randrange(self.prefix[-1])
        index = bisect_right(self.prefix, ticket)
        offset = ticket - (self.prefix[index - 1] if index else 0)
        x1, y1, x2, _ = self.rects[index]
        width = x2 - x1 + 1
        return [x1 + offset % width, y1 + offset // width]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
