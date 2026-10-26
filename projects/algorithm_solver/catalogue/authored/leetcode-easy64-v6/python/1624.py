"""1624. Largest Substring Between Two Equal Characters (Easy).

Specification: https://leetcode.com/problems/largest-substring-between-two-equal-characters/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space for the lowercase ASCII alphabet."""
    first_indices = [-1] * 26
    longest = -1
    for index, character in enumerate(s):
        letter = ord(character) - ord('a')
        if first_indices[letter] == -1:
            first_indices[letter] = index
        else:
            longest = max(longest, index - first_indices[letter] - 1)
    return longest


class Solution:
    def maxLengthBetweenEqualCharacters(self, s: str) -> int:
        return solve(s)
