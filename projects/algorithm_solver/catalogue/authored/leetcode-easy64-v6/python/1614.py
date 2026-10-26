"""1614. Maximum Nesting Depth of the Parentheses (Easy).

Specification: https://leetcode.com/problems/maximum-nesting-depth-of-the-parentheses/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; input is a valid parentheses string."""
    depth = 0
    maximum = 0
    for character in s:
        if character == '(':
            depth += 1
            maximum = max(maximum, depth)
        elif character == ')':
            depth -= 1
    return maximum


class Solution:
    def maxDepth(self, s: str) -> int:
        return solve(s)
