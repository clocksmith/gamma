"""792. Number of Matching Subsequences (Medium).

Specification: https://leetcode.com/problems/number-of-matching-subsequences/description/
"""


def _is_subsequence(word, s):
    i = 0
    for ch in s:
        if i < len(word) and ch == word[i]:
            i += 1
    return i == len(word)


def solve(s: str, words: list[str]) -> int:
    return sum(1 for word in words if _is_subsequence(word, s))


class Solution:
    def numMatchingSubseq(self, s: str, words: list[str]) -> int:
        return solve(s, words)
