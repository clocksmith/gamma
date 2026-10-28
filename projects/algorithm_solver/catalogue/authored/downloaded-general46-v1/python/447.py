"""447. Number of Boomerangs (Medium).

Specification: https://leetcode.com/problems/number-of-boomerangs/description/
"""


def solve(points: list[list[int]]) -> int:
    total = 0
    for x1, y1 in points:
        counts = {}
        for x2, y2 in points:
            distance = (x1 - x2) ** 2 + (y1 - y2) ** 2
            counts[distance] = counts.get(distance, 0) + 1
        for count in counts.values():
            total += count * (count - 1)
    return total


class Solution:
    def numberOfBoomerangs(self, points: list[list[int]]) -> int:
        return solve(points)
