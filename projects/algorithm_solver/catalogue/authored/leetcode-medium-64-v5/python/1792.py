"""1792. Maximum Average Pass Ratio: assign each extra student to the largest exact marginal gain."""
from heapq import heapify, heappop, heappush


class _ClassState:
    __slots__ = ('passed', 'total', 'index')

    def __init__(self, passed: int, total: int, index: int):
        self.passed = passed
        self.total = total
        self.index = index

    def __lt__(self, other):
        left = (self.total - self.passed) * other.total * (other.total + 1)
        right = (other.total - other.passed) * self.total * (self.total + 1)
        return left > right or (left == right and self.index < other.index)


def solve(classes: list[list[int]], extraStudents: int) -> float:
    """O((n + e) * log(n + 1)) time and O(n) space, with e extra students; inputs are read-only."""
    heap = [_ClassState(passed, total, index) for index, (passed, total) in enumerate(classes)]
    heapify(heap)
    for _ in range(extraStudents):
        current = heappop(heap)
        current.passed += 1
        current.total += 1
        heappush(heap, current)
    return sum(current.passed / current.total for current in heap) / len(classes)


class Solution:
    def maxAverageRatio(self, classes: list[list[int]], extraStudents: int) -> float:
        return solve(classes, extraStudents)
