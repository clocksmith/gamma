"""3623. Count Number of Trapezoids I.

Specification: https://leetcode.com/problems/count-number-of-trapezoids-i/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) expected time and space; horizontal trapezoids from pairs on distinct y levels.
Inputs are not modified.
"""

from collections import Counter

def solve(points):
    levels = Counter(y for x, y in points)
    previous = answer = 0
    modulus = 1000000007
    for count in levels.values():
        pairs = count * (count - 1) // 2
        answer = (answer + previous * pairs) % modulus
        previous = (previous + pairs) % modulus
    return answer


class Solution:
    def countTrapezoids(self, points):
        return solve(points)
