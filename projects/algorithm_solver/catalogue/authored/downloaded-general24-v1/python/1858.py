"""1858. Longest Word With All Prefixes (Medium).

Specification: https://leetcode.com/problems/longest-word-with-all-prefixes/description/
"""


def solve(words: list[str]) -> str:
    word_set = set(words)
    candidates = sorted(words, key=lambda w: (-len(w), w))
    for word in candidates:
        ok = True
        for length in range(1, len(word)):
            if word[:length] not in word_set:
                ok = False
                break
        if ok:
            return word
    return ''


class Solution:
    def longestWord(self, words: list[str]) -> str:
        return solve(words)
