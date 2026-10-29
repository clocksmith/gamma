"""Hack2Hire 6854ca09c201117d348a25d5 (Longest Semi-Alternating Substring) over an INFERRED spec; qualification unknown."""

def solve(s):
    best, start = 0, 0
    for i in range(len(s)):
        if i >= 2 and s[i] == s[i - 1] == s[i - 2]:
            start = i - 1
        if i - start + 1 > best:
            best = i - start + 1
    return best


class Solution:
    def longestSemiAlternating(self, s):
        return solve(s)
