"""973. K Closest Points to Origin (Medium).

Specification: https://leetcode.com/problems/k-closest-points-to-origin/description/
"""


def solve(points: list[list[int]], k: int) -> list[list[int]]:
    ordered = sorted(points, key=lambda p: (p[0] * p[0] + p[1] * p[1], p[0], p[1]))
    return ordered[:k]


class Solution:
    def kClosest(self, points: list[list[int]], k: int) -> list[list[int]]:
        return solve(points, k)
