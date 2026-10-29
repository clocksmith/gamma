"""Hack2Hire 68ac67eb1bf7d2097f647efe (Randomly Partition Array) over an INFERRED spec; qualification unknown."""


def solve(nums, k, randomInts):
    shuffled = list(nums)
    n = len(shuffled)
    step = 0
    for i in range(n - 1, 0, -1):
        j = randomInts[step] % (i + 1)
        step += 1
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    size = n // k
    return [shuffled[s * size:(s + 1) * size] for s in range(k)]


class Solution:
    def randomPartition(self, nums, k, randomInts):
        return solve(nums, k, randomInts)
