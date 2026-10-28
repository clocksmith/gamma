"""56. Merge Intervals (Medium).

Specification: https://leetcode.com/problems/merge-intervals/description/
"""


def solve(intervals: list[list[int]]) -> list[list[int]]:
    ordered = sorted(intervals)
    result = []
    for interval in ordered:
        if not result or interval[0] > result[-1][1]:
            result.append(interval[:])
        else:
            result[-1][1] = max(result[-1][1], interval[1])
    return result


class Solution:
    def merge(self, intervals: list[list[int]]) -> list[list[int]]:
        return solve(intervals)
