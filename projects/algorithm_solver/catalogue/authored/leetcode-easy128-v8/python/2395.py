"""2395. Find Subarrays With Equal Sum (Easy).

Specification: https://leetcode.com/problems/find-subarrays-with-equal-sum/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) expected time, O(n) space; two equal sums of adjacent pairs identify distinct subarrays."""
    seen = set()
    for index in range(1, len(nums)):
        total = nums[index - 1] + nums[index]
        if total in seen:
            return True
        seen.add(total)
    return False


class Solution:
    def findSubarrays(self, nums: list[int]) -> bool:
        return solve(nums)
