"""20. Valid Parentheses (Easy).

Specification: https://leetcode.com/problems/valid-parentheses/description/
"""


def solve(s: str) -> bool:
    """O(n) time and space; match closing brackets against the latest unmatched opening."""
    opening = {')': '(', ']': '[', '}': '{'}
    stack = []
    for character in s:
        if character in '([{':
            stack.append(character)
        elif not stack or stack.pop() != opening[character]:
            return False
    return not stack


class Solution:
    def isValid(self, s: str) -> bool:
        return solve(s)
