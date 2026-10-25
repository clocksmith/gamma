"""2351. First Letter to Appear Twice (Easy).

Specification: https://leetcode.com/problems/first-letter-to-appear-twice/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(1) alphabet space; return the earliest second occurrence."""
    seen = [False] * 26
    for character in s:
        index = ord(character) - ord('a')
        if seen[index]:
            return character
        seen[index] = True
    return ''


class Solution:
    def repeatedCharacter(self, s: str) -> str:
        return solve(s)
