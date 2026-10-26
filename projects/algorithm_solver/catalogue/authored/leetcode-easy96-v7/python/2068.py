"""2068. Check Whether Two Strings are Almost Equivalent (Easy).

Specification: https://leetcode.com/problems/check-whether-two-strings-are-almost-equivalent/description/
"""


def solve(word1: str, word2: str) -> bool:
    """O(n + m) time, O(1) space for 26 lowercase letters; every frequency difference is at most three."""
    difference = [0] * 26
    for character in word1:
        difference[ord(character) - 97] += 1
    for character in word2:
        difference[ord(character) - 97] -= 1
    return all(abs(count) <= 3 for count in difference)


class Solution:
    def checkAlmostEquivalent(self, word1: str, word2: str) -> bool:
        return solve(word1, word2)
