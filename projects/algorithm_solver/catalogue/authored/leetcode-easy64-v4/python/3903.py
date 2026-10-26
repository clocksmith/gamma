"""3903. Smallest Stable Index I (Easy).

Specification: https://leetcode.com/problems/smallest-stable-index-i/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and space; both prefix maximum and suffix minimum include the candidate index."""
    suffixMinimum = [0] * len(nums)
    suffixMinimum[-1] = nums[-1]
    for index in range(len(nums) - 2, -1, -1):
        suffixMinimum[index] = min(nums[index], suffixMinimum[index + 1])
    prefixMaximum = nums[0]
    for index, value in enumerate(nums):
        prefixMaximum = max(prefixMaximum, value)
        if prefixMaximum - suffixMinimum[index] <= k:
            return index
    return -1


class Solution:
    def firstStableIndex(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
