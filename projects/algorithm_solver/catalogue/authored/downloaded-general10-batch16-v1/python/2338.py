"""2338. Count the Number of Ideal Arrays (Hard).

Specification: https://leetcode.com/problems/count-the-number-of-ideal-arrays/description/
"""


def solve(n: int, maxValue: int) -> int:
    MOD = 1000000007
    prev = [0] + [1] * maxValue
    for _len in range(2, n + 1):
        cur = [0] * (maxValue + 1)
        for d in range(1, maxValue + 1):
            for m in range(d, maxValue + 1, d):
                cur[m] = (cur[m] + prev[d]) % MOD
        prev = cur
    return sum(prev[1:]) % MOD


class Solution:
    def idealArrays(self, n, maxValue) -> object:
        return solve(n, maxValue)
