"""1637. Widest Vertical Area Between Two Points Containing No Points (Medium).

Specification: https://leetcode.com/problems/widest-vertical-area-between-two-points-containing-no-points/description/
"""


def solve(points: list[list[int]]) -> int:
    xs = sorted(x for x, _y in points)
    best = 0
    for i in range(1, len(xs)):
        best = max(best, xs[i] - xs[i - 1])
    return best


class Solution:
    def maxWidthOfVerticalArea(self, points: list[list[int]]) -> int:
        return solve(points)
