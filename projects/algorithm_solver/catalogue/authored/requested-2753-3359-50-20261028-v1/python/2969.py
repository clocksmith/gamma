"""Original frontend 2969 variant; qualification unknown."""

from collections import deque


def solve(prices) -> int:
    n = len(prices)
    q = deque([(n + 1, 0)])
    for i in range(n, 0, -1):
        while q and q[0][0] > 2 * i + 1:
            q.popleft()
        cur = prices[i - 1] + q[0][1]
        while q and q[-1][1] >= cur:
            q.pop()
        q.append((i, cur))
    return q[-1][1]


minimumCoins = solve


class Solution:
    def minimumCoins(self, prices) -> int:
        return solve(prices)
