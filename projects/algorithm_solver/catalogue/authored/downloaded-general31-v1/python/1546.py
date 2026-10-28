"""1546. Maximum Number of Non-Overlapping Subarrays With Sum Equals Target (Medium).

Specification: https://leetcode.com/problems/maximum-number-of-non-overlapping-subarrays-with-sum-equals-target/description/
"""


def solve(nums: list[int], target: int) -> int:
    seen = {0}
    prefix = 0
    count = 0
    for value in nums:
        prefix += value
        if prefix - target in seen:
            count += 1
            seen = {prefix}
        else:
            seen.add(prefix)
    return count


class Solution:
    def maxNonOverlapping(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
