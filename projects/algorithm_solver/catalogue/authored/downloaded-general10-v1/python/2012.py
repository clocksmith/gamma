"""2012. Sum of Beauty in the Array (Medium).

Specification: https://leetcode.com/problems/sum-of-beauty-in-the-array/description/
"""


def solve(nums: list[int]) -> int:
    n = len(nums)
    pref_max = [0] * n
    suff_min = [0] * n
    cur = float("-inf")
    for i in range(n):
        pref_max[i] = cur
        cur = max(cur, nums[i])
    cur = float("inf")
    for i in range(n - 1, -1, -1):
        suff_min[i] = cur
        cur = min(cur, nums[i])
    total = 0
    for i in range(1, n - 1):
        if pref_max[i] < nums[i] < suff_min[i]:
            total += 2
        elif nums[i - 1] < nums[i] < nums[i + 1]:
            total += 1
    return total


class Solution:
    def sumOfBeauties(self, nums: list[int]) -> int:
        return solve(nums)
