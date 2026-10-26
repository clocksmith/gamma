"""1986. Minimum Number of Work Sessions to Finish the Tasks: minimize the session count and then the current load for every task subset."""


def solve(tasks: list[int], sessionTime: int) -> int:
    """O(n * 2^n) time and O(2^n) auxiliary space; inputs are read-only."""
    count = len(tasks)
    best = [(count + 1, sessionTime)] * (1 << count)
    best[0] = (1, 0)
    for mask in range(1 << count):
        sessions, used = best[mask]
        for index, duration in enumerate(tasks):
            bit = 1 << index
            if mask & bit:
                continue
            candidate = (sessions, used + duration) if used + duration <= sessionTime else (sessions + 1, duration)
            next_mask = mask | bit
            if candidate < best[next_mask]:
                best[next_mask] = candidate
    return best[-1][0]


class Solution:
    def minSessions(self, tasks: list[int], sessionTime: int) -> int:
        return solve(tasks, sessionTime)
