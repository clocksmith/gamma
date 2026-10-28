"""1155. Number of Dice Rolls With Target Sum (Medium).

Specification: https://leetcode.com/problems/number-of-dice-rolls-with-target-sum/description/
"""


MOD = 1000000007


def solve(n: int, k: int, target: int) -> int:
    dp = [0] * (target + 1)
    dp[0] = 1
    for _die in range(n):
        nxt = [0] * (target + 1)
        for total in range(target + 1):
            if dp[total] == 0:
                continue
            for face in range(1, k + 1):
                if total + face <= target:
                    nxt[total + face] = (nxt[total + face] + dp[total]) % MOD
        dp = nxt
    return dp[target]


class Solution:
    def numRollsToTarget(self, n: int, k: int, target: int) -> int:
        return solve(n, k, target)
