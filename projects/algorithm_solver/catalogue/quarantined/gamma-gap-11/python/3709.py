"""3709. Design Exam Scores Tracker.

O(1) amortized record, O(log n) query, O(n) space. Prefix sums remain exact below 1e14.
"""
from __future__ import annotations
from bisect import bisect_left, bisect_right


class ExamTracker:
    def __init__(self):
        self.times = []
        self.prefix = [0]

    def record(self, time: int, score: int) -> None:
        self.times.append(time)
        self.prefix.append(self.prefix[-1] + score)

    def totalScore(self, startTime: int, endTime: int) -> int:
        left = bisect_left(self.times, startTime)
        right = bisect_right(self.times, endTime)
        return self.prefix[right] - self.prefix[left]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native interface with one request-local instance."""
    if not operations:
        return []
    instance = ExamTracker(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = ExamTracker
