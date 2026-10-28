"""1114. Number of Ways to Stay in the Same Place After Some Steps (Medium).

Specification: https://leetcode.com/problems/number-of-ways-to-stay-in-the-same-place-after-some-steps/description/
"""


def solve(steps: int, arrLen: int) -> int:
    modulus = 1000000007
    max_position = min(steps, arrLen - 1)
    dp = [0] * (max_position + 1)
    dp[0] = 1
    for _step in range(steps):
        nxt = [0] * (max_position + 1)
        for position in range(max_position + 1):
            if dp[position] == 0:
                continue
            nxt[position] = (nxt[position] + dp[position]) % modulus
            if position > 0:
                nxt[position - 1] = (nxt[position - 1] + dp[position]) % modulus
            if position < max_position:
                nxt[position + 1] = (nxt[position + 1] + dp[position]) % modulus
        dp = nxt
    return dp[0]


class Solution:
    def numWays(self, steps: int, arrLen: int) -> int:
        return solve(steps, arrLen)
