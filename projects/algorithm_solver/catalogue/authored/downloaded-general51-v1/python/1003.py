"""1003. Check If Word Is Valid After Substitutions (Medium).

Specification: https://leetcode.com/problems/check-if-word-is-valid-after-substitutions/description/
"""


def solve(s: str) -> bool:
    stack = []
    for ch in s:
        stack.append(ch)
        while len(stack) >= 3 and stack[-3] == 'a' and stack[-2] == 'b' and stack[-1] == 'c':
            del stack[-3:]
    return len(stack) == 0


class Solution:
    def isValid(self, s: str) -> bool:
        return solve(s)
