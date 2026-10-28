"""939. Minimum Area Rectangle (Medium).

Specification: https://leetcode.com/problems/minimum-area-rectangle/description/
"""


def solve(points: list[list[int]]) -> int:
    point_set = {(x, y) for x, y in points}
    best = float('inf')
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            x1, y1 = points[i]
            x2, y2 = points[j]
            if x1 == x2 or y1 == y2:
                continue
            if (x1, y2) in point_set and (x2, y1) in point_set:
                best = min(best, abs(x2 - x1) * abs(y2 - y1))
    return 0 if best == float('inf') else best


class Solution:
    def minAreaRect(self, points: list[list[int]]) -> int:
        return solve(points)
