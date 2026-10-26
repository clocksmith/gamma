"""1544. Make The String Great (Easy).

Specification: https://leetcode.com/problems/make-the-string-great/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(n) space; input contains only upper/lowercase ASCII letters."""
    stack = []
    for character in s:
        if stack and abs(ord(stack[-1]) - ord(character)) == 32:
            stack.pop()
        else:
            stack.append(character)
    return ''.join(stack)


class Solution:
    def makeGood(self, s: str) -> str:
        return solve(s)
