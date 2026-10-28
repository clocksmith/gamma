"""820. Short Encoding of Words (Medium).

Specification: https://leetcode.com/problems/short-encoding-of-words/description/
"""


def solve(words: list[str]) -> int:
    unique = set(words)
    for word in words:
        for i in range(1, len(word)):
            unique.discard(word[i:])
    return sum(len(word) + 1 for word in unique)


class Solution:
    def minimumLengthEncoding(self, words: list[str]) -> int:
        return solve(words)
