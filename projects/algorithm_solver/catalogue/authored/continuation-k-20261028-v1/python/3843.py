from collections import Counter


def solve(nums):
    counts = Counter(nums)
    frequencies = Counter(counts.values())
    return next((x for x in nums if frequencies[counts[x]] == 1), -1)


class Solution:
    def firstUniqueFreq(self, nums):
        return solve(nums)
