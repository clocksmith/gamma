"""362. Design Hit Counter."""
from collections import deque

class HitCounter:
    def __init__(self):
        self.hits = deque()

    def _expire(self, timestamp: int) -> None:
        while self.hits and self.hits[0] <= timestamp - 300:
            self.hits.popleft()

    def hit(self, timestamp: int) -> None:
        self.hits.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        self._expire(timestamp)
        return len(self.hits)

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    counter = HitCounter()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'HitCounter':
            result.append(None)
        else:
            result.append(getattr(counter, operation)(*values))
    return result
