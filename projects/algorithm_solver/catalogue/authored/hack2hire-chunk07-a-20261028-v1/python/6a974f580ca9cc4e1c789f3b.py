"""Hack2Hire 6a974f580ca9cc4e1c789f3b (Longest Subarray Under Limit) over an INFERRED spec; qualification unknown."""

def solve(a, k):
    best, left, total = 0, 0, 0
    for right, v in enumerate(a):
        total += v
        while total > k:
            total -= a[left]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


class Solution:
    def longestSubarrayUnderLimit(self, a, k):
        return solve(a, k)
