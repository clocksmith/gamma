"""1165. Single-Row Keyboard (Easy).

Specification: https://leetcode.com/problems/single-row-keyboard/description/
"""


def solve(keyboard: str, word: str) -> int:
    """O(word length + 26) time, O(26) space; start the finger at keyboard index zero."""
    positions = [0] * 26
    for index, character in enumerate(keyboard):
        positions[ord(character) - 97] = index
    previous = 0
    total = 0
    for character in word:
        current = positions[ord(character) - 97]
        total += abs(current - previous)
        previous = current
    return total


class Solution:
    def calculateTime(self, keyboard: str, word: str) -> int:
        return solve(keyboard, word)
