"""1446. Consecutive Characters (Easy).

Specification: https://leetcode.com/problems/consecutive-characters/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; track the longest equal-character run."""
    longest = 0
    length = 0
    previous = ''
    for character in s:
        length = length + 1 if character == previous else 1
        previous = character
        longest = max(longest, length)
    return longest


class Solution:
    def maxPower(self, s: str) -> int:
        return solve(s)
