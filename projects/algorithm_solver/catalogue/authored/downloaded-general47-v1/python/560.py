"""560. Subarray Sum Equals K (Medium).

Specification: https://leetcode.com/problems/subarray-sum-equals-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    counts = {0: 1}
    prefix = 0
    result = 0
    for value in nums:
        prefix += value
        result += counts.get(prefix - k, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return result


class Solution:
    def subarraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
