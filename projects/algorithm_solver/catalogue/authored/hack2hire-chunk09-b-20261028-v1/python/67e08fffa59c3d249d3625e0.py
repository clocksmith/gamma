"""Hack2Hire 67e08fffa59c3d249d3625e0 (Count Distinct Elements in Window) over an INFERRED spec; qualification unknown."""


def solve(nums, k):
    counts = {}
    distinct = 0
    out = []
    for i, value in enumerate(nums):
        c = counts.get(value, 0)
        if c == 0:
            distinct += 1
        counts[value] = c + 1
        if i >= k:
            old = nums[i - k]
            c = counts[old] - 1
            counts[old] = c
            if c == 0:
                distinct -= 1
        if i >= k - 1:
            out.append(distinct)
    return out


class Solution:
    def countDistinct(self, nums, k):
        return solve(nums, k)
