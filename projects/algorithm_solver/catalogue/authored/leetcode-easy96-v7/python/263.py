"""263. Ugly Number (Easy).

Specification: https://leetcode.com/problems/ugly-number/description/
"""


def solve(n: int) -> bool:
    """O(log n) time, O(1) space; remove only factors 2, 3, and 5."""
    if n <= 0:
        return False
    value = n
    for factor in (2, 3, 5):
        while value % factor == 0:
            value //= factor
    return value == 1


class Solution:
    def isUgly(self, n: int) -> bool:
        return solve(n)
