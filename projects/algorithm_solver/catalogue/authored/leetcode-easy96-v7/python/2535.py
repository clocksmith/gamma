"""2535. Difference Between Element Sum and Digit Sum of an Array (Easy).

Specification: https://leetcode.com/problems/difference-between-element-sum-and-digit-sum-of-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n * d) time, O(1) space for at most d digits per value; preserve nums."""
    element_sum = 0
    digit_sum = 0
    for value in nums:
        element_sum += value
        remaining = value
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
    return abs(element_sum - digit_sum)


class Solution:
    def differenceOfSum(self, nums: list[int]) -> int:
        return solve(nums)
