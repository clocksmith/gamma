"""Hack2Hire 6a1f3ca28b879849ebc10ffb (Find Pattern Matching Words) over an INFERRED spec; qualification unknown."""


def solve(wordDict, pattern):
    m = len(pattern)
    out = []
    for word in wordDict:
        previous = [True] + [False] * m
        for ch in word:
            current = [False] * (m + 1)
            for j in range(1, m + 1):
                p = pattern[j - 1]
                if p == '.':  # consume its first character, or extend an already started run
                    current[j] = previous[j - 1] or previous[j]
                else:
                    current[j] = previous[j - 1] and (p == '?' or p == ch)
            previous = current
        if previous[m]:
            out.append(word)
    return out


class Solution:
    def findPatternMatchingWords(self, wordDict, pattern):
        return solve(wordDict, pattern)
