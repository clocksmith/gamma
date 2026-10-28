"""1249. Minimum Remove to Make Valid Parentheses (Medium).

Specification: https://leetcode.com/problems/minimum-remove-to-make-valid-parentheses/description/
"""


def solve(s: str) -> str:
    remove = set()
    stack = []
    for i, ch in enumerate(s):
        if ch == '(':
            stack.append(i)
        elif ch == ')':
            if not stack:
                remove.add(i)
            else:
                stack.pop()
    for index in stack:
        remove.add(index)
    return "".join(ch for i, ch in enumerate(s) if i not in remove)


class Solution:
    def minRemoveToMakeValid(self, s: str) -> str:
        return solve(s)
