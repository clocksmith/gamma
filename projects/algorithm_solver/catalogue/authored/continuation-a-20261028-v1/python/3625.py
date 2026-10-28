from collections import defaultdict
from math import gcd

def solve(points):
    directions = defaultdict(int)
    lines = defaultdict(int)
    midpoints = defaultdict(int)
    midpoint_directions = defaultdict(int)
    parallel_pairs = parallelograms = 0
    for i, (x, y) in enumerate(points):
        for u, v in points[i + 1:]:
            dx, dy = u - x, v - y
            divisor = gcd(abs(dx), abs(dy))
            dx, dy = dx // divisor, dy // divisor
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            direction = (dx, dy)
            line = (dx, dy, dx * y - dy * x)
            midpoint = (x + u, y + v)
            midpoint_direction = (x + u, y + v, dx, dy)
            parallel_pairs += directions[direction] - lines[line]
            parallelograms += midpoints[midpoint] - midpoint_directions[midpoint_direction]
            directions[direction] += 1
            lines[line] += 1
            midpoints[midpoint] += 1
            midpoint_directions[midpoint_direction] += 1
    return parallel_pairs - parallelograms


class Solution:
    def countTrapezoids(self, points):
        return solve(points)
