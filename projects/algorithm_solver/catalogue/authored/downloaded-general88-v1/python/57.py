"""57. Insert Interval (Medium).

Specification: https://leetcode.com/problems/insert-interval/description/
"""


def solve(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
    result = []
    inserted = newInterval[:]
    used = False
    for interval in intervals:
        if interval[1] < inserted[0]:
            result.append(interval[:])
        elif interval[0] > inserted[1]:
            if not used:
                result.append(inserted)
                used = True
            result.append(interval[:])
        else:
            inserted = [min(inserted[0], interval[0]), max(inserted[1], interval[1])]
    if not used:
        result.append(inserted)
    return result


class Solution:
    def insert(self, intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
        return solve(intervals, newInterval)
