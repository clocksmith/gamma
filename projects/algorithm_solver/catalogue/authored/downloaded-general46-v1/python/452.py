"""452. Minimum Number of Arrows to Burst Balloons (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/description/
"""


def solve(points: list[list[int]]) -> int:
    if not points:
        return 0
    ordered = sorted(points, key=lambda p: p[1])
    arrows = 1
    end = ordered[0][1]
    for i in range(1, len(ordered)):
        if ordered[i][0] > end:
            arrows += 1
            end = ordered[i][1]
    return arrows


class Solution:
    def findMinArrowShots(self, points: list[list[int]]) -> int:
        return solve(points)
