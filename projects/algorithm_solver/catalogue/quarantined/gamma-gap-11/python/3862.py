"""3862. Find the Smallest Balanced Index."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) space; positive suffix products saturate above every possible prefix sum, without overflowing."""
    left = sum(nums)
    cap = left + 1
    product = 1
    answer = -1
    for index in range(len(nums) - 1, -1, -1):
        left -= nums[index]
        if left == product:
            answer = index
        product = cap if product > (cap - 1) // nums[index] else product * nums[index]
    return answer


class Solution:
    def smallestBalancedIndex(self, nums: list[int]) -> int:
        return solve(nums)
