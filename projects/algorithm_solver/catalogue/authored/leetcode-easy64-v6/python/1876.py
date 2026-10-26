"""1876. Substrings of Size Three with Distinct Characters (Easy).

Specification: https://leetcode.com/problems/substrings-of-size-three-with-distinct-characters/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; count each length-three occurrence independently."""
    result = 0
    for index in range(2, len(s)):
        if s[index - 2] != s[index - 1] and s[index - 2] != s[index] and s[index - 1] != s[index]:
            result += 1
    return result


class Solution:
    def countGoodSubstrings(self, s: str) -> int:
        return solve(s)
