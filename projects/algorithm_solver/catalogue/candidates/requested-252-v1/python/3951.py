"""3951. Minimum Energy to Maintain Brightness
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-energy-to-maintain-brightness/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3951.Minimum%20Energy%20to%20Maintain%20Brightness/README_EN.md
Complexity: O(q log q) time, O(q) space.
Inclusive integer times; overlapping requirements count once. Brightness <= n guarantees ceil(brightness/3) bulbs suffice. Maximum energy below 3.34e14 is exactly representable. Inputs preserved.
"""

from __future__ import annotations

def solve(n, brightness, intervals):
    ordered = sorted((start, end) for start, end in intervals)
    left, right = ordered[0]
    duration = 0
    for start, end in ordered[1:]:
        if start > right + 1:
            duration += right - left + 1
            left, right = start, end
        else:
            right = max(right, end)
    duration += right - left + 1
    return duration * ((brightness + 2) // 3)


class Solution:
    def minEnergy(self, n, brightness, intervals):
        return solve(n, brightness, intervals)
