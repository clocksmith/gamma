"""2873. Maximum Value of an Ordered Triplet I (Easy).

Specification: https://leetcode.com/problems/maximum-value-of-an-ordered-triplet-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; update triplet, pair, then prefix to keep indices strictly ordered."""
    largest_prefix = largest_difference = best = 0
    for value in nums:
        best = max(best, largest_difference * value)
        largest_difference = max(largest_difference, largest_prefix - value)
        largest_prefix = max(largest_prefix, value)
    return best


class Solution:
    def maximumTripletValue(self, nums: list[int]) -> int:
        return solve(nums)
