"""1611. Make The String Great (Easy).

Specification: https://leetcode.com/problems/make-the-string-great/description/
"""


def solve(s: str) -> str:
    stack = []
    for ch in s:
        if stack and stack[-1] != ch and stack[-1].lower() == ch.lower():
            stack.pop()
        else:
            stack.append(ch)
    return "".join(stack)


class Solution:
    def makeGood(self, s: str) -> str:
        return solve(s)
