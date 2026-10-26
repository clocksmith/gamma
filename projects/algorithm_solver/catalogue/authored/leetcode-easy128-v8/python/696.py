"""696. Count Binary Substrings (Easy).

Specification: https://leetcode.com/problems/count-binary-substrings/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; each adjacent pair of runs contributes its smaller length."""
    previous = 0
    current = 1
    total = 0
    for index in range(1, len(s)):
        if s[index] == s[index - 1]:
            current += 1
        else:
            total += min(previous, current)
            previous, current = current, 1
    return total + min(previous, current)


class Solution:
    def countBinarySubstrings(self, s: str) -> int:
        return solve(s)
