"""1828. Queries on Number of Points Inside a Circle: compare squared distances without rounding or removing duplicate points."""


def solve(points: list[list[int]], queries: list[list[int]]) -> list[int]:
    """O(p * q) time and O(q) output space with O(1) auxiliary space; inputs are read-only."""
    result = []
    for center_x, center_y, radius in queries:
        squared_radius = radius * radius
        count = 0
        for x, y in points:
            dx, dy = x - center_x, y - center_y
            if dx * dx + dy * dy <= squared_radius:
                count += 1
        result.append(count)
    return result


class Solution:
    def countPoints(self, points: list[list[int]], queries: list[list[int]]) -> list[int]:
        return solve(points, queries)
