"""Hack2Hire 6a51443a665efda9311f60c6 (Suffix Maximum Count) over an INFERRED spec; qualification unknown."""


def solve(nums, query):
    n = len(nums)
    counts = [0] * n
    best = nums[n - 1]
    count = 0
    for i in range(n - 1, -1, -1):
        v = nums[i]
        if v > best:
            best = v
            count = 1
        elif v == best:
            count += 1
        counts[i] = count
    return [counts[q] for q in query]


class Solution:
    def suffixMaxCount(self, nums, query):
        return solve(nums, query)
