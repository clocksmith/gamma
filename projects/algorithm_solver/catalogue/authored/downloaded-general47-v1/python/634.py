"""634. Find the Derangement of Numbers (Medium).

Specification: https://leetcode.com/problems/find-the-derangement-of-numbers/description/
"""


def solve(n: int) -> int:
    MOD = 1000000007
    if n == 0:
        return 1
    if n == 1:
        return 0
    previous, current = 1, 0
    for i in range(2, n + 1):
        nxt = ((i - 1) * (previous + current)) % MOD
        previous, current = current, nxt
    return current


class Solution:
    def findDerangement(self, n: int) -> int:
        return solve(n)
