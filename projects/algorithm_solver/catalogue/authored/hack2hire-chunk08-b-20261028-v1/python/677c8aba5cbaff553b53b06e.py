"""Hack2Hire 677c8aba5cbaff553b53b06e (Subset Sum Equals K) over an INFERRED spec; qualification unknown."""

def solve(nums, k):
    total = sum(nums)
    if k > total:
        return False
    target = min(k, total - k)
    mask = (1 << (target + 1)) - 1
    reach = 1
    for x in nums:
        if x <= target:
            reach |= (reach << x) & mask
            if reach >> target & 1:
                return True
    return bool(reach >> target & 1)


class Solution:
    def subsetSumExists(self, nums, k):
        return solve(nums, k)
