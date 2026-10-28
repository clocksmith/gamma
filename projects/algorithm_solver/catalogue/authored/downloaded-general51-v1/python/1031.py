"""1031. Maximum Sum of Two Non-Overlapping Subarrays (Medium).

Specification: https://leetcode.com/problems/maximum-sum-of-two-non-overlapping-subarrays/description/
"""


def solve(nums: list[int], firstLen: int, secondLen: int) -> int:
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)

    def subarray_sum(start, length):
        return prefix[start + length] - prefix[start]

    best = float('-inf')
    for i in range(len(nums) - firstLen + 1):
        for j in range(len(nums) - secondLen + 1):
            if i + firstLen <= j or j + secondLen <= i:
                best = max(best, subarray_sum(i, firstLen) + subarray_sum(j, secondLen))
    return best


class Solution:
    def maxSumTwoNoOverlap(self, nums: list[int], firstLen: int, secondLen: int) -> int:
        return solve(nums, firstLen, secondLen)
