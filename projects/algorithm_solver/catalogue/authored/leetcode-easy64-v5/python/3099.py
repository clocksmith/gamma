"""3099. Harshad Number (Easy).

Specification: https://leetcode.com/problems/harshad-number/description/
"""


def solve(x: int) -> int:
    """O(d) time, O(1) auxiliary space; d is the decimal digit count of positive x."""
    remaining = x
    digit_sum = 0
    while remaining > 0:
        digit_sum += remaining % 10
        remaining //= 10
    return digit_sum if x % digit_sum == 0 else -1


class Solution:
    def sumOfTheDigitsOfHarshadNumber(self, x: int) -> int:
        return solve(x)
