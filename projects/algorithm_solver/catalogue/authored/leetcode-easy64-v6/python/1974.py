"""1974. Minimum Time to Type Word Using Special Typewriter (Easy).

Specification: https://leetcode.com/problems/minimum-time-to-type-word-using-special-typewriter/description/
"""


def solve(word: str) -> int:
    """O(n) time, O(1) space; choose the shorter circular movement and pay one second per letter."""
    position = 0
    seconds = 0
    for character in word:
        target = ord(character) - ord('a')
        distance = abs(target - position)
        seconds += min(distance, 26 - distance) + 1
        position = target
    return seconds


class Solution:
    def minTimeToType(self, word: str) -> int:
        return solve(word)
