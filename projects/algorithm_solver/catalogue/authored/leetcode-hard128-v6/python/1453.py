"""1453. Maximum Number of Darts Inside of a Circular Dartboard.

Enumerate circle centers fixed by two boundary points; O(n^3) time, O(1) auxiliary space. Inputs are preserved.
"""

from math import sqrt


def solve(darts: list[list[int]], r: int) -> int:
    radius_squared = r * r
    tolerance = 1e-7

    def count(x, y):
        return sum((a - x) ** 2 + (b - y) ** 2 <= radius_squared + tolerance for a, b in darts)

    answer = max((count(x, y) for x, y in darts), default=0)
    for index, (x1, y1) in enumerate(darts):
        for other in range(index + 1, len(darts)):
            x2, y2 = darts[other]
            dx, dy = x2 - x1, y2 - y1
            distance_squared = dx * dx + dy * dy
            if not distance_squared or distance_squared > 4 * radius_squared:
                continue
            scale = sqrt(max(0.0, radius_squared / distance_squared - 0.25))
            middle_x, middle_y = (x1 + x2) / 2, (y1 + y2) / 2
            answer = max(answer, count(middle_x - dy * scale, middle_y + dx * scale),
                         count(middle_x + dy * scale, middle_y - dx * scale))
    return answer


class Solution:
    def numPoints(self, darts: list[list[int]], r: int) -> int:
        return solve(darts, r)
