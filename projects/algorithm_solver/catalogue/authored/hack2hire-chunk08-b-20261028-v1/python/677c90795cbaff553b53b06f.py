"""Hack2Hire 677c90795cbaff553b53b06f (Subset Sum Equals K) over an INFERRED spec; qualification unknown."""

MOD = 1000000007


def solve(nums, k):
    total = sum(nums)
    if k > total:
        return 0
    target = min(k, total - k)
    ways = [0] * (target + 1)
    ways[0] = 1
    reach = 0
    for x in nums:
        reach = min(target, reach + x)
        for s in range(reach, x - 1, -1):
            v = ways[s] + ways[s - x]
            ways[s] = v - MOD if v >= MOD else v
    return ways[target]


class Solution:
    def countSubsets(self, nums, k):
        return solve(nums, k)
