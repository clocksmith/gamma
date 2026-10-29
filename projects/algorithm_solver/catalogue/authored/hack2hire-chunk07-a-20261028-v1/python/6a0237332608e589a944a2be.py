"""Hack2Hire 6a0237332608e589a944a2be (Longest Common Subsequence-Substring) over an INFERRED spec; qualification unknown."""

def solve(x, y):
    m = len(y)
    prev = [0] * (m + 1)  # prev[j]: longest substring of y ending at j that is a subsequence of the processed prefix of x
    for ch in x:
        cur = [0]
        for j in range(m):
            cur.append(prev[j] + 1 if y[j] == ch else prev[j + 1])
        prev = cur
    return max(prev)


class Solution:
    def longestSubsequenceSubstring(self, x, y):
        return solve(x, y)
