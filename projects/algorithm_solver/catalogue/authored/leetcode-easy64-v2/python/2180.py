"""2180. Count Integers With Even Digit Sum (Easy).

Specification: https://leetcode.com/problems/count-integers-with-even-digit-sum/description/
"""


def solve(num: int) -> int:
    """O(num * d) time, O(1) space; d is the digit count of num."""
    result = 0
    for value in range(1, num + 1):
        remaining = value
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        if digit_sum % 2 == 0:
            result += 1
    return result


class Solution:
    def countEven(self, num: int) -> int:
        return solve(num)
