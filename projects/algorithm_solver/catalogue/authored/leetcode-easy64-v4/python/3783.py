"""3783. Mirror Distance of an Integer (Easy).

Specification: https://leetcode.com/problems/mirror-distance-of-an-integer/description/
"""


def solve(n: int) -> int:
    """O(d) time, O(1) space; d is the decimal digit count; use exact integer arithmetic."""
    remaining = n
    reversed = 0
    while remaining > 0:
        reversed = reversed * 10 + remaining % 10
        remaining //= 10
    return abs(n - reversed)


class Solution:
    def mirrorDistance(self, n: int) -> int:
        return solve(n)
