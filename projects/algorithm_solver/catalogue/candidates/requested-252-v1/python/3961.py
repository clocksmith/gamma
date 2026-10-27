"""3961. Maximize Sum of Device Ratings
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximize-sum-of-device-ratings/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3961.Maximize%20Sum%20of%20Device%20Ratings/README_EN.md
Complexity: O(total units) time, O(1) auxiliary space.
One transfer maximum per source; the lowest-second-minimum device receives all discarded minima. Single-unit devices cannot improve by transfers. Inputs preserved.
"""

from __future__ import annotations

def solve(units):
    if len(units[0]) == 1:
        return sum(row[0] for row in units)
    smallest = float('inf')
    smallest_second = float('inf')
    total = 0
    for row in units:
        first = second = float('inf')
        for value in row:
            if value < first:
                first, second = value, first
            elif value < second:
                second = value
        smallest = min(smallest, first)
        smallest_second = min(smallest_second, second)
        total += second
    return total - smallest_second + smallest


class Solution:
    def maxRatings(self, units):
        return solve(units)
