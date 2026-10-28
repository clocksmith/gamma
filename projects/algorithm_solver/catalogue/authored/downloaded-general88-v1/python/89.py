"""89. Gray Code (Medium).

Specification: https://leetcode.com/problems/gray-code/description/
"""


def solve(n: int) -> list[int]:
    return [i ^ (i >> 1) for i in range(1 << n)]


class Solution:
    def grayCode(self, n: int) -> list[int]:
        return solve(n)
