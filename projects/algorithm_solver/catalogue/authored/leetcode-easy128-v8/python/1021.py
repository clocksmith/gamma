"""1021. Remove Outermost Parentheses (Easy).

Specification: https://leetcode.com/problems/remove-outermost-parentheses/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; omit the opening and closing parentheses at primitive depth zero."""
    depth = 0
    result = []
    for character in s:
        if character == '(':
            if depth > 0:
                result.append(character)
            depth += 1
        else:
            depth -= 1
            if depth > 0:
                result.append(character)
    return ''.join(result)


class Solution:
    def removeOuterParentheses(self, s: str) -> str:
        return solve(s)
