"""720. Longest Word in Dictionary (Easy).

Specification: https://leetcode.com/problems/longest-word-in-dictionary/description/
"""


def solve(words: list[str]) -> str:
    ordered = sorted(words, key=lambda w: (-len(w), w))
    built = set(words)
    for word in ordered:
        if all(word[:i] in built for i in range(1, len(word))):
            return word
    return ''


class Solution:
    def longestWord(self, words: list[str]) -> str:
        return solve(words)
