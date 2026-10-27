"""281. Zigzag Iterator."""
from collections import deque

class ZigzagIterator:
    def __init__(self, v1: list[int], v2: list[int]):
        self.queue = deque()
        if v1:
            self.queue.append((v1, 0))
        if v2:
            self.queue.append((v2, 0))

    def next(self) -> int:
        values, index = self.queue.popleft()
        value = values[index]
        if index + 1 < len(values):
            self.queue.append((values, index + 1))
        return value

    def hasNext(self) -> bool:
        return bool(self.queue)

def solve(v1: list[int], v2: list[int]) -> list[int]:
    iterator = ZigzagIterator(v1, v2)
    result = []
    while iterator.hasNext():
        result.append(iterator.next())
    return result
