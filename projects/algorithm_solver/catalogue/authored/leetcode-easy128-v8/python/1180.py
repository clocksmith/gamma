"""1180. Count Substrings with Only One Distinct Letter (Easy).

Specification: https://leetcode.com/problems/count-substrings-with-only-one-distinct-letter/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; the current equal-character run counts substrings ending here."""
    run = total = 0
    for index, character in enumerate(s):
        run = run + 1 if index > 0 and character == s[index - 1] else 1
        total += run
    return total


class Solution:
    def countLetters(self, s: str) -> int:
        return solve(s)
