"""935. Knight Dialer (Medium).

Specification: https://leetcode.com/problems/knight-dialer/description/
"""


MOVES = {0: [4, 6], 1: [6, 8], 2: [7, 9], 3: [4, 8], 4: [3, 9, 0], 5: [], 6: [1, 7, 0], 7: [2, 6], 8: [1, 3], 9: [2, 4]}


def solve(n: int) -> int:
    MOD = 1000000007
    dp = [1] * 10
    for _step in range(1, n):
        nxt = [0] * 10
        for digit in range(10):
            for dest in MOVES[digit]:
                nxt[dest] = (nxt[dest] + dp[digit]) % MOD
        dp = nxt
    return sum(dp) % MOD


class Solution:
    def knightDialer(self, n: int) -> int:
        return solve(n)
