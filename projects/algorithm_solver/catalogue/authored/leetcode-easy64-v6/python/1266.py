"""1266. Minimum Time Visiting All Points (Easy).

Specification: https://leetcode.com/problems/minimum-time-visiting-all-points/description/
"""


def solve(points: list[list[int]]) -> int:
    """O(n) time, O(1) space; preserve points and their order."""
    result = 0
    for index in range(1, len(points)):
        delta_x = abs(points[index][0] - points[index - 1][0])
        delta_y = abs(points[index][1] - points[index - 1][1])
        result += max(delta_x, delta_y)
    return result


class Solution:
    def minTimeToVisitAllPoints(self, points: list[list[int]]) -> int:
        return solve(points)
