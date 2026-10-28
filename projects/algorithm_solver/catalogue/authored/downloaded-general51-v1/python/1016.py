"""1016. Binary String With Substrings Representing 1 To N (Medium).

Specification: https://leetcode.com/problems/binary-string-with-substrings-representing-1-to-n/description/
"""


def solve(s: str, n: int) -> bool:
    for value in range(1, n + 1):
        if bin(value)[2:] not in s:
            return False
    return True


class Solution:
    def queryString(self, s: str, n: int) -> bool:
        return solve(s, n)
