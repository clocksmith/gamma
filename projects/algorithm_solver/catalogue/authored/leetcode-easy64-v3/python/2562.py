"""2562. Find the Array Concatenation Value (Easy).

Specification: https://leetcode.com/problems/find-the-array-concatenation-value/description/
"""


def solve(nums: list[int]) -> int:
    """O(n log M) time, O(1) space; arithmetic concatenation preserves nums."""
    left, right = 0, len(nums) - 1
    total = 0
    while left < right:
        place = 10
        while place <= nums[right]:
            place *= 10
        total += nums[left] * place + nums[right]
        left += 1
        right -= 1
    if left == right:
        total += nums[left]
    return total


class Solution:
    def findTheArrayConcVal(self, nums: list[int]) -> int:
        return solve(nums)
