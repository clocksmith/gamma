"""3498. Reverse Degree of a String (Easy).

Specification: https://leetcode.com/problems/reverse-degree-of-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; multiply reverse-alphabet values by one-based positions."""
    total = 0
    for index, character in enumerate(s):
        total += (ord('z') - ord(character) + 1) * (index + 1)
    return total


class Solution:
    def reverseDegree(self, s: str) -> int:
        return solve(s)
