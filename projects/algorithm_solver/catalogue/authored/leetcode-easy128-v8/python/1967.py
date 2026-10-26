"""1967. Number of Strings That Appear as Substrings in Word (Easy).

Specification: https://leetcode.com/problems/number-of-strings-that-appear-as-substrings-in-word/description/
"""


def solve(patterns: list[str], word: str) -> int:
    """O(word length * total pattern length) worst-case time, O(1) auxiliary space; count repeated pattern entries separately."""
    count = 0
    for pattern in patterns:
        if pattern in word:
            count += 1
    return count


class Solution:
    def numOfStrings(self, patterns: list[str], word: str) -> int:
        return solve(patterns, word)
