"""1221. Split a String in Balanced Strings (Easy).

Specification: https://leetcode.com/problems/split-a-string-in-balanced-strings/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; split at every zero balance."""
    balance = 0
    result = 0
    for character in s:
        balance += 1 if character == 'L' else -1
        if balance == 0:
            result += 1
    return result


class Solution:
    def balancedStringSplit(self, s: str) -> int:
        return solve(s)
