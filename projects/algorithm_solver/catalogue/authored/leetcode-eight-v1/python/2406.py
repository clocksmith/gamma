"""The minimum interval-group count equals peak inclusive overlap."""


def solve(intervals: list[list[int]]) -> int:
    """O(n log n) time and O(n) space; sort copies, never the caller's rows."""
    starts = sorted(left for left, _ in intervals)
    ends = sorted(right for _, right in intervals)
    start = end = active = best = 0
    while start < len(starts):
        # Equal endpoints overlap: process a start before an equal end.
        if starts[start] <= ends[end]:
            active += 1
            start += 1
            best = max(best, active)
        else:
            active -= 1
            end += 1
    return best


class Solution:
    def minGroups(self, intervals: list[list[int]]) -> int:
        return solve(intervals)
