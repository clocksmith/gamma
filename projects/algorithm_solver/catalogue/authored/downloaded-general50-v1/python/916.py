"""916. Word Subsets (Medium).

Specification: https://leetcode.com/problems/word-subsets/description/
"""


def _counts(word):
    c = {}
    for ch in word:
        c[ch] = c.get(ch, 0) + 1
    return c


def solve(words1: list[str], words2: list[str]) -> list[str]:
    need = {}
    for word in words2:
        c = _counts(word)
        for ch, v in c.items():
            need[ch] = max(need.get(ch, 0), v)
    result = []
    for word in words1:
        c = _counts(word)
        if all(c.get(ch, 0) >= v for ch, v in need.items()):
            result.append(word)
    return result


class Solution:
    def wordSubsets(self, words1: list[str], words2: list[str]) -> list[str]:
        return solve(words1, words2)
