"""3798. Largest Even Number (Easy).

Specification: https://leetcode.com/problems/largest-even-number/description/
"""


def solve(s: str) -> str:
    """O(n) time and output space; the input alphabet contains only 1 and 2."""
    end = len(s)
    while end > 0 and s[end - 1] != '2':
        end -= 1
    return s[:end]


class Solution:
    def largestEven(self, s: str) -> str:
        return solve(s)
