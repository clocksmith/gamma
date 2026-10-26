"""1370. Increasing Decreasing String (Easy).

Specification: https://leetcode.com/problems/increasing-decreasing-string/description/
"""


def solve(s: str) -> str:
    """O(n) time for the fixed 26-letter alphabet, O(n) result space."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - 97] += 1
    result = []
    while len(result) < len(s):
        for letter in range(26):
            if counts[letter] > 0:
                result.append(chr(97 + letter))
                counts[letter] -= 1
        for letter in range(25, -1, -1):
            if counts[letter] > 0:
                result.append(chr(97 + letter))
                counts[letter] -= 1
    return ''.join(result)


class Solution:
    def sortString(self, s: str) -> str:
        return solve(s)
