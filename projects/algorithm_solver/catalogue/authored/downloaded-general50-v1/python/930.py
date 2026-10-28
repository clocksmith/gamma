"""930. Binary Subarrays With Sum (Medium).

Specification: https://leetcode.com/problems/binary-subarrays-with-sum/description/
"""


def solve(nums: list[int], goal: int) -> int:
    counts = {0: 1}
    prefix = 0
    total = 0
    for v in nums:
        prefix += v
        total += counts.get(prefix - goal, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return total


class Solution:
    def numSubarraysWithSum(self, nums: list[int], goal: int) -> int:
        return solve(nums, goal)
