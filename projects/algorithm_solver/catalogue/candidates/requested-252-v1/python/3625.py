"""3625. Count Number of Trapezoids II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-number-of-trapezoids-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3625.Count%20Number%20of%20Trapezoids%20II/README_EN.md
Complexity: O(n^2 log C) time for normalized integer directions; O(n^2) space.
Inputs preserved. Integer line keys avoid floating-point slope equality. Counts fit Number for n <= 500.
"""

from __future__ import annotations
from math import gcd

def solve(points):
    slopes, lines, midpoints, midpoint_slopes = {}, {}, {}, {}
    parallel_pairs = parallelograms = 0
    for i, (x1, y1) in enumerate(points):
        for x2, y2 in points[:i]:
            dx, dy = x2 - x1, y2 - y1
            divisor = gcd(abs(dx), abs(dy))
            dx, dy = dx // divisor, dy // divisor
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            slope = (dx, dy)
            line = (dx, dy, dx * y1 - dy * x1)
            middle = (x1 + x2, y1 + y2)
            middle_slope = (middle, slope)
            parallel_pairs += slopes.get(slope, 0) - lines.get(line, 0)
            parallelograms += midpoints.get(middle, 0) - midpoint_slopes.get(middle_slope, 0)
            slopes[slope] = slopes.get(slope, 0) + 1
            lines[line] = lines.get(line, 0) + 1
            midpoints[middle] = midpoints.get(middle, 0) + 1
            midpoint_slopes[middle_slope] = midpoint_slopes.get(middle_slope, 0) + 1
    return parallel_pairs - parallelograms


class Solution:
    def countTrapezoids(self, points):
        return solve(points)
