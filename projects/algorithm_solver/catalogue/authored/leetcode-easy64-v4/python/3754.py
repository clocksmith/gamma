"""3754. Concatenate Non-Zero Digits and Multiply by Sum I (Easy).

Specification: https://leetcode.com/problems/concatenate-non-zero-digits-and-multiply-by-sum-i/description/
"""


def solve(n: int) -> int:
    """O(d) time, O(1) space; the result fits exactly in JavaScript Number, not necessarily int32."""
    remaining = n
    compact = 0
    digitSum = 0
    place = 1
    while remaining > 0:
        digit = remaining % 10
        digitSum += digit
        if digit != 0:
            compact += digit * place
            place *= 10
        remaining //= 10
    return compact * digitSum


class Solution:
    def sumAndMultiply(self, n: int) -> int:
        return solve(n)
