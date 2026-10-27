"""436. Find Right Interval."""

from bisect import bisect_left, bisect_right

def solve(intervals: list[list[int]]) -> list[int]:
    ordered = sorted((interval[0], index) for index, interval in enumerate(intervals))
    starts = [item[0] for item in ordered]
    answer = []
    for _, end in intervals:
        index = bisect_left(starts, end)
        answer.append(ordered[index][1] if index < len(ordered) else -1)
    return answer


class Solution:
    def findRightInterval(self, intervals: list[list[int]]) -> list[int]:
        return solve(intervals)
