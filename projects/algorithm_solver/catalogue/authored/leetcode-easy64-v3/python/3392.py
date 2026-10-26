"""3392. Count Subarrays of Length Three With a Condition (Easy).

Specification: https://leetcode.com/problems/count-subarrays-of-length-three-with-a-condition/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; multiply the outer sum by two to avoid fractional division."""
    result = 0
    for index in range(1, len(nums) - 1):
        if 2 * (nums[index - 1] + nums[index + 1]) == nums[index]:
            result += 1
    return result


class Solution:
    def countSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
