"""890. Find and Replace Pattern (Medium).

Specification: https://leetcode.com/problems/find-and-replace-pattern/description/
"""


def _matches(word, pattern):
    w2p = {}
    p2w = {}
    for w, p in zip(word, pattern):
        if w in w2p and w2p[w] != p:
            return False
        if p in p2w and p2w[p] != w:
            return False
        w2p[w] = p
        p2w[p] = w
    return True


def solve(words: list[str], pattern: str) -> list[str]:
    return [w for w in words if _matches(w, pattern)]


class Solution:
    def findAndReplacePattern(self, words: list[str], pattern: str) -> list[str]:
        return solve(words, pattern)
