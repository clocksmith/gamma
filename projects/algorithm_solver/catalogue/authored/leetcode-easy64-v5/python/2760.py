"""2760. Longest Even Odd Subarray With Threshold (Easy).

Specification: https://leetcode.com/problems/longest-even-odd-subarray-with-threshold/description/
"""


def solve(nums: list[int], threshold: int) -> int:
    """O(n) time, O(1) auxiliary space; preserve nums."""
    length = 0
    longest = 0
    for index, value in enumerate(nums):
        if value > threshold:
            length = 0
        elif length > 0 and value % 2 != nums[index - 1] % 2:
            length += 1
        else:
            length = 1 if value % 2 == 0 else 0
        longest = max(longest, length)
    return longest


class Solution:
    def longestAlternatingSubarray(self, nums: list[int], threshold: int) -> int:
        return solve(nums, threshold)
