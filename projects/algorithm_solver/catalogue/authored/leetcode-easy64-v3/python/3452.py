"""3452. Sum of Good Numbers (Easy).

Specification: https://leetcode.com/problems/sum-of-good-numbers/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time, O(1) space; compare only existing neighbors at distance k."""
    total = 0
    for index, value in enumerate(nums):
        if index >= k and value <= nums[index - k]:
            continue
        if index + k < len(nums) and value <= nums[index + k]:
            continue
        total += value
    return total


class Solution:
    def sumOfGoodNumbers(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
