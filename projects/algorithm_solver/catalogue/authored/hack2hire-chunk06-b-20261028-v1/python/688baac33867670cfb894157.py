"""Hack2Hire 688baac33867670cfb894157 (Longest Circular Sequence of Ones) over an INFERRED spec; qualification unknown."""

def solve(nums, k):
    n = len(nums)
    if nums.count(0) <= k:
        return n
    best, left, zeros = 0, 0, 0
    for right in range(2 * n):
        if nums[right % n] == 0:
            zeros += 1
        while zeros > k:
            if nums[left % n] == 0:
                zeros -= 1
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


class Solution:
    def longestCircularOnes(self, nums, k):
        return solve(nums, k)
