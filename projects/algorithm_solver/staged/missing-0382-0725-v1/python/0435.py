"""435. Non-overlapping Intervals. Greedily retain earliest-finishing intervals; input is preserved."""

def solve(intervals: list[list[int]]) -> int:
    end = float('-inf')
    removed = 0
    for left, right in sorted(intervals, key=lambda interval: interval[1]):
        if left < end:
            removed += 1
        else:
            end = right
    return removed


class Solution:
    def eraseOverlapIntervals(self, intervals: list[list[int]]) -> int:
        return solve(intervals)
