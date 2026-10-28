"""2549. Count Distinct Numbers on Board (Easy).

Specification: https://leetcode.com/problems/count-distinct-numbers-on-board/description/
"""


def solve(n):
    # Starting from n, each step adds n-1, then n-2, and so on down to 2;
    # for n = 1 nothing new appears.
    return max(n - 1, 1)


class Solution:
    def distinctIntegers(self, n):
        return solve(n)
