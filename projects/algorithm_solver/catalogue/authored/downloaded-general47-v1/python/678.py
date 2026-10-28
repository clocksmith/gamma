"""678. Valid Parenthesis String (Medium).

Specification: https://leetcode.com/problems/valid-parenthesis-string/description/
"""


def solve(s: str) -> bool:
    low = 0
    high = 0
    for ch in s:
        if ch == '(':
            low += 1
            high += 1
        elif ch == ')':
            low -= 1
            high -= 1
        else:
            low -= 1
            high += 1
        if high < 0:
            return False
        low = max(low, 0)
    return low == 0


class Solution:
    def checkValidString(self, s: str) -> bool:
        return solve(s)
