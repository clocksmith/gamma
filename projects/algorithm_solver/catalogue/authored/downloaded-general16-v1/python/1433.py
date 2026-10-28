"""1433. Check If a String Can Break Another String (Medium).

Specification: https://leetcode.com/problems/check-if-a-string-can-break-another-string/description/
"""


def solve(s1, s2):
    a = sorted(s1)
    b = sorted(s2)
    a_breaks = all(x >= y for x, y in zip(a, b))
    b_breaks = all(y >= x for x, y in zip(a, b))
    return a_breaks or b_breaks


class Solution:
    def checkIfCanBreak(self, s1, s2):
        return solve(s1, s2)
