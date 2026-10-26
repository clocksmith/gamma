"""258. Add Digits (Easy).

Specification: https://leetcode.com/problems/add-digits/description/
"""


def solve(num: int) -> int:
    """O(1) time and space; the digital root of a nonnegative integer."""
    return 0 if num == 0 else 1 + (num - 1) % 9


class Solution:
    def addDigits(self, num: int) -> int:
        return solve(num)
