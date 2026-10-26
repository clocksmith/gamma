"""812. Largest Triangle Area (Easy).

Specification: https://leetcode.com/problems/largest-triangle-area/description/
"""


def solve(points: list[list[int]]) -> float:
    """O(n^3) time, O(1) auxiliary space; maximize the absolute integer cross product."""
    largest_double_area = 0
    for first in range(len(points) - 2):
        for second in range(first + 1, len(points) - 1):
            for third in range(second + 1, len(points)):
                ax, ay = points[first]
                bx, by = points[second]
                cx, cy = points[third]
                double_area = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
                largest_double_area = max(largest_double_area, double_area)
    return largest_double_area / 2


class Solution:
    def largestTriangleArea(self, points: list[list[int]]) -> float:
        return solve(points)
