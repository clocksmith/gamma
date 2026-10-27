"""452. Minimum Number of Arrows to Burst Balloons."""

def solve(points: list[list[int]]) -> int:
    end = None
    arrows = 0
    for left, right in sorted(points, key=lambda item: item[1]):
        if end is None or left > end:
            end = right
            arrows += 1
    return arrows


class Solution:
    def findMinArrowShots(self, points: list[list[int]]) -> int:
        return solve(points)
