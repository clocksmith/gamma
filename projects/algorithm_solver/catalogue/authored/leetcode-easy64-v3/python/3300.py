"""3300. Minimum Element After Replacement With Digit Sum (Easy).

Specification: https://leetcode.com/problems/minimum-element-after-replacement-with-digit-sum/description/
"""


def solve(nums: list[int]) -> int:
    """O(n log M) time, O(1) space; compute replacement values without changing nums."""
    smallest = float('inf')
    for value in nums:
        remaining = value
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        smallest = min(smallest, digit_sum)
    return smallest


class Solution:
    def minElement(self, nums: list[int]) -> int:
        return solve(nums)
