"""1610. Maximum Number of Visible Points: sorted polar-angle sliding window; O(n log n) time and O(n) space."""

from math import atan2, degrees


def solve(points: list[list[int]], angle: int, location: list[int]) -> int:
    if angle >= 360:
        return len(points)
    origin_x, origin_y = location
    coincident = 0
    directions = []
    for x, y in points:
        if x == origin_x and y == origin_y:
            coincident += 1
        else:
            directions.append(degrees(atan2(y - origin_y, x - origin_x)))
    directions.sort()
    size = len(directions)
    extended = directions + [value + 360 for value in directions]
    left = answer = 0
    for right, value in enumerate(extended):
        while right - left >= size or value - extended[left] > angle + 1e-10:
            left += 1
        answer = max(answer, right - left + 1)
    return answer + coincident


class Solution:
    def visiblePoints(self, points: list[list[int]], angle: int, location: list[int]) -> int:
        return solve(points, angle, location)
