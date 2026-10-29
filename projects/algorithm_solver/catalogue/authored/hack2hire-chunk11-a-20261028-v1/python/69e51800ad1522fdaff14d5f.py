"""Hack2Hire 69e51800ad1522fdaff14d5f (Find Size of Largest Subset) over an INFERRED spec; qualification unknown."""


def solve(arr):
    best = 0
    for bit in range(31):
        count = sum((v >> bit) & 1 for v in arr)
        if count > best:
            best = count
    return best


class Solution:
    def findLargestSubsetSize(self, arr):
        return solve(arr)
