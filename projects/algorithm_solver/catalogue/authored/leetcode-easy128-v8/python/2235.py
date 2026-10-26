"""2235. Add Two Integers (Easy).

Specification: https://leetcode.com/problems/add-two-integers/description/
"""


def solve(num1: int, num2: int) -> int:
    """O(1) time and space; exact integer addition over the declared input range."""
    return num1 + num2


class Solution:
    def sum(self, num1: int, num2: int) -> int:
        return solve(num1, num2)
