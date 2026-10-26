"""844. Backspace String Compare (Easy).

Specification: https://leetcode.com/problems/backspace-string-compare/description/
"""


def solve(s: str, t: str) -> bool:
    """O(n + m) time and space; build each final string with a backspace-aware stack."""
    def render(text):
        stack = []
        for character in text:
            if character == '#':
                if stack:
                    stack.pop()
            else:
                stack.append(character)
        return ''.join(stack)

    return render(s) == render(t)


class Solution:
    def backspaceCompare(self, s: str, t: str) -> bool:
        return solve(s, t)
