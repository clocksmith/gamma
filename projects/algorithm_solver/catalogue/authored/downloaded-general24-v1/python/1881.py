"""1881. Maximum Value after Insertion (Medium).

Specification: https://leetcode.com/problems/maximum-value-after-insertion/description/
"""


def solve(n: str, x: int) -> str:
    negative = n[0] == '-'
    digit = str(x)
    for i, ch in enumerate(n):
        if ch == '-':
            continue
        if not negative and ch < digit:
            return n[:i] + digit + n[i:]
        if negative and ch > digit:
            return n[:i] + digit + n[i:]
    return n + digit


class Solution:
    def maxValue(self, n: str, x: int) -> str:
        return solve(n, x)
