"""435. Non-overlapping Intervals (Medium).

Specification: https://leetcode.com/problems/non-overlapping-intervals/description/
"""


def solve(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals, key=lambda p: p[1])
    kept = 1
    end = ordered[0][1]
    for i in range(1, len(ordered)):
        if ordered[i][0] >= end:
            kept += 1
            end = ordered[i][1]
    return len(intervals) - kept


class Solution:
    def eraseOverlapIntervals(self, intervals: list[list[int]]) -> int:
        return solve(intervals)
