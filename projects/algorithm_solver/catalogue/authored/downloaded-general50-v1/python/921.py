"""921. Minimum Add to Make Parentheses Valid (Medium).

Specification: https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/description/
"""


def solve(s: str) -> int:
    open_count = 0
    needed = 0
    for ch in s:
        if ch == '(':
            open_count += 1
        elif open_count > 0:
            open_count -= 1
        else:
            needed += 1
    return open_count + needed


class Solution:
    def minAddToMakeValid(self, s: str) -> int:
        return solve(s)
