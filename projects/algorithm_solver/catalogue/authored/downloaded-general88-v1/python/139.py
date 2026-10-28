"""139. Word Break (Medium).

Specification: https://leetcode.com/problems/word-break/description/
"""


def solve(s: str, wordDict: list[str]) -> bool:
    words = set(wordDict)
    dp = [False] * (len(s) + 1)
    dp[0] = True
    for i in range(1, len(s) + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
    return dp[len(s)]


class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> bool:
        return solve(s, wordDict)
