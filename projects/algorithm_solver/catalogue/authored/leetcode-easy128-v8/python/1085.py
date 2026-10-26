"""1085. Sum of Digits in the Minimum Number (Easy).

Specification: https://leetcode.com/problems/sum-of-digits-in-the-minimum-number/description/
"""


def solve(nums: list[int]) -> int:
    """O(n + d) time, O(1) space; return one exactly when the minimum digit sum is even."""
    smallest = min(nums)
    digit_sum = 0
    while smallest > 0:
        digit_sum += smallest % 10
        smallest //= 10
    return 1 if digit_sum % 2 == 0 else 0


class Solution:
    def sumOfDigits(self, nums: list[int]) -> int:
        return solve(nums)
