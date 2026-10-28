"""961. N-Repeated Element in Size 2N Array (Easy).

Specification: https://leetcode.com/problems/n-repeated-element-in-size-2n-array/description/
"""


def solve(nums: list[int]) -> int:
    counts = {}
    best = nums[0]
    best_count = 0
    for v in nums:
        counts[v] = counts.get(v, 0) + 1
        if counts[v] > best_count:
            best_count = counts[v]
            best = v
    return best


class Solution:
    def repeatedNTimes(self, nums: list[int]) -> int:
        return solve(nums)
