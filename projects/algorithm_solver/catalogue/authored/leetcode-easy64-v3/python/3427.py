"""3427. Sum of Variable Length Subarrays (Easy).

Specification: https://leetcode.com/problems/sum-of-variable-length-subarrays/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time and space; prefix sums evaluate the subarray ending at every index."""
    prefix = [0]
    total = 0
    for index, value in enumerate(nums):
        prefix.append(prefix[-1] + value)
        start = max(0, index - value)
        total += prefix[index + 1] - prefix[start]
    return total


class Solution:
    def subarraySum(self, nums: list[int]) -> int:
        return solve(nums)
