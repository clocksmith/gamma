"""1272. Remove Interval (Medium).

Specification: https://leetcode.com/problems/remove-interval/description/
"""


def solve(intervals: list[list[int]], toBeRemoved: list[int]) -> list[list[int]]:
    remove_start, remove_end = toBeRemoved
    result = []
    for start, end in intervals:
        if end <= remove_start or start >= remove_end:
            result.append([start, end])
        else:
            if start < remove_start:
                result.append([start, remove_start])
            if end > remove_end:
                result.append([remove_end, end])
    return result


class Solution:
    def removeInterval(self, intervals: list[list[int]], toBeRemoved: list[int]) -> list[list[int]]:
        return solve(intervals, toBeRemoved)
