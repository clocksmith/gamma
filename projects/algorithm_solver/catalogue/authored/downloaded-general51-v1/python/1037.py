"""1037. Valid Boomerang (Easy).

Specification: https://leetcode.com/problems/valid-boomerang/description/
"""


def solve(points: list[list[int]]) -> bool:
    (x1, y1), (x2, y2), (x3, y3) = points
    if (x1 == x2 and y1 == y2) or (x1 == x3 and y1 == y3) or (x2 == x3 and y2 == y3):
        return False
    return (x2 - x1) * (y3 - y1) != (y2 - y1) * (x3 - x1)


class Solution:
    def isBoomerang(self, points: list[list[int]]) -> bool:
        return solve(points)
