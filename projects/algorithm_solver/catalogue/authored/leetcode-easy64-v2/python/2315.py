"""2315. Count Asterisks (Easy).

Specification: https://leetcode.com/problems/count-asterisks/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; ignore asterisks inside paired vertical bars."""
    outside = True
    result = 0
    for character in s:
        if character == '|':
            outside = not outside
        elif character == '*' and outside:
            result += 1
    return result


class Solution:
    def countAsterisks(self, s: str) -> int:
        return solve(s)
