# 312 — Burst Balloons. Original implementation; authored candidate, not independently qualified.
def solve(nums):
    values = [1] + list(nums) + [1]
    n = len(values)
    dp = [[0] * n for _ in range(n)]
    # k is the LAST balloon removed from the open interval (left, right).
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            dp[left][right] = max(dp[left][k] + values[left] * values[k] * values[right] + dp[k][right]
                                  for k in range(left + 1, right))
    return dp[0][-1]

maxCoins = solve

class Solution:
    maxCoins = staticmethod(solve)
