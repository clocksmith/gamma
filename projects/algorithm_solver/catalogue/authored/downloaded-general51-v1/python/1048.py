"""1048. Longest String Chain (Medium).

Specification: https://leetcode.com/problems/longest-string-chain/description/
"""


def solve(words: list[str]) -> int:
    ordered = sorted(words, key=len)
    dp = {}
    best = 1
    for word in ordered:
        length = 1
        for i in range(len(word)):
            predecessor = word[:i] + word[i + 1:]
            if predecessor in dp:
                length = max(length, dp[predecessor] + 1)
        dp[word] = length
        best = max(best, length)
    return best


class Solution:
    def longestStrChain(self, words: list[str]) -> int:
        return solve(words)
