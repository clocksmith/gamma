"""387. First Unique Character in a String (Easy).

Specification: https://leetcode.com/problems/first-unique-character-in-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space for lowercase-English input; preserve original indices."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - 97] += 1
    for index, character in enumerate(s):
        if counts[ord(character) - 97] == 1:
            return index
    return -1


class Solution:
    def firstUniqChar(self, s: str) -> int:
        return solve(s)
