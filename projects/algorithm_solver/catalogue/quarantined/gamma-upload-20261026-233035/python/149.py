"""149. Max Points on a Line."""
from collections import defaultdict
from math import gcd

def solve(points: list[list[int]]) -> int:
    if len(points) <= 2:
        return len(points)
    best = 0
    for index, (x1, y1) in enumerate(points):
        slopes = defaultdict(int)
        duplicates = 1
        local = 0
        for x2, y2 in points[index + 1:]:
            dx, dy = x2 - x1, y2 - y1
            if dx == 0 and dy == 0:
                duplicates += 1
                continue
            divisor = gcd(dx, dy)
            dx //= divisor
            dy //= divisor
            if dx < 0 or dx == 0 and dy < 0:
                dx, dy = -dx, -dy
            slopes[(dy, dx)] += 1
            local = max(local, slopes[(dy, dx)])
        best = max(best, local + duplicates)
    return best

class Solution:
    def maxPoints(self, points: list[list[int]]) -> int:
        return solve(points)
