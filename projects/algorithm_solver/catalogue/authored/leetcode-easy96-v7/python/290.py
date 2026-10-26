"""290. Word Pattern (Easy).

Specification: https://leetcode.com/problems/word-pattern/description/
"""


def solve(pattern: str, s: str) -> bool:
    """O(n + m) time and space for the input text; require a character-to-word bijection."""
    words = s.split(' ')
    if len(words) != len(pattern):
        return False
    forward = {}
    backward = {}
    for character, word in zip(pattern, words):
        if character in forward and forward[character] != word:
            return False
        if word in backward and backward[word] != character:
            return False
        forward[character] = word
        backward[word] = character
    return True


class Solution:
    def wordPattern(self, pattern: str, s: str) -> bool:
        return solve(pattern, s)
