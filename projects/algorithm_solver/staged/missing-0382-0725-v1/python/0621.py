"""621. Task Scheduler."""

from collections import Counter

def solve(tasks: list[str], n: int) -> int:
    if not tasks:
        return 0
    counts = Counter(tasks)
    maximum = max(counts.values())
    tied = sum(value == maximum for value in counts.values())
    return max(len(tasks), (maximum - 1) * (n + 1) + tied)


class Solution:
    def leastInterval(self, tasks: list[str], n: int) -> int:
        return solve(tasks, n)
