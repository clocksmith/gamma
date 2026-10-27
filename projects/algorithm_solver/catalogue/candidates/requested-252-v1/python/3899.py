"""3899. Angles of a Triangle
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/angles-of-a-triangle/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3899.Angles%20of%20a%20Triangle/README_EN.md
Complexity: O(1) time and space.
Positive sides <=1000. Returns floating point degrees; tolerance-based comparison required, not exact JS/Python bytes. Input preserved.
"""

from __future__ import annotations
from math import acos, degrees

def solve(sides):
    a, b, c = sorted(sides)
    if a + b <= c:
        return []
    result = []
    for opposite, first, second in [(a, b, c), (b, a, c), (c, a, b)]:
        cosine = (first * first + second * second - opposite * opposite) / (2 * first * second)
        result.append(degrees(acos(max(-1.0, min(1.0, cosine)))))
    return result


class Solution:
    def internalAngles(self, sides):
        return solve(sides)
