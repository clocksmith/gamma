"""436. Find Right Interval (Medium).

Specification: https://leetcode.com/problems/find-right-interval/description/
"""


def solve(intervals: list[list[int]]) -> list[int]:
    starts = sorted((interval[0], index) for index, interval in enumerate(intervals))
    result = []
    for interval in intervals:
        left, right = 0, len(starts) - 1
        answer = -1
        while left <= right:
            mid = (left + right) // 2
            if starts[mid][0] >= interval[1]:
                answer = starts[mid][1]
                right = mid - 1
            else:
                left = mid + 1
        result.append(answer)
    return result


class Solution:
    def findRightInterval(self, intervals: list[list[int]]) -> list[int]:
        return solve(intervals)
