"""2278. Percentage of Letter in String (Easy).

Specification: https://leetcode.com/problems/percentage-of-letter-in-string/description/
"""


def solve(s: str, letter: str) -> int:
    """O(n) time, O(1) space; round the nonnegative percentage down."""
    count = 0
    for character in s:
        if character == letter:
            count += 1
    return 100 * count // len(s)


class Solution:
    def percentageLetter(self, s: str, letter: str) -> int:
        return solve(s, letter)
