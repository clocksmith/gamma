"""279. Perfect Squares."""
from math import isqrt

def solve(n: int) -> int:
    squares = [value * value for value in range(1, isqrt(n) + 1)]
    dp = list(range(n + 1))
    for value in range(1, n + 1):
        for square in squares:
            if square > value:
                break
            dp[value] = min(dp[value], dp[value - square] + 1)
    return dp[n]

class Solution:
    def numSquares(self, n: int) -> int:
        return solve(n)
