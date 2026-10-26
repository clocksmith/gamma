"""1779. Find Nearest Point That Has the Same X or Y Coordinate (Easy).

Specification: https://leetcode.com/problems/find-nearest-point-that-has-the-same-x-or-y-coordinate/description/
"""


def solve(x: int, y: int, points: list[list[int]]) -> int:
    """O(n) time, O(1) space; equal distances keep the first index; preserve points."""
    best_index = -1
    best_distance = None
    for index, (point_x, point_y) in enumerate(points):
        if point_x != x and point_y != y:
            continue
        distance = abs(point_x - x) + abs(point_y - y)
        if best_distance is None or distance < best_distance:
            best_index = index
            best_distance = distance
    return best_index


class Solution:
    def nearestValidPoint(self, x: int, y: int, points: list[list[int]]) -> int:
        return solve(x, y, points)
