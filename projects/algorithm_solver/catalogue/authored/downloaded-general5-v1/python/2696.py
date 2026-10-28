"""2696. Minimum String Length After Removing Substrings (Easy).

Specification: https://leetcode.com/problems/minimum-string-length-after-removing-substrings/description/
"""


def solve(s: str) -> int:
    stack = []
    for ch in s:
        top = stack[-1] if stack else ''
        if (top == 'A' and ch == 'B') or (top == 'C' and ch == 'D'):
            stack.pop()
        else:
            stack.append(ch)
    return len(stack)


class Solution:
    def minLength(self, s: str) -> int:
        return solve(s)
