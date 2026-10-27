"""629. K Inverse Pairs Array. Sliding-window insertion-count dynamic programming with inversion symmetry."""

def solve(n: int, k: int) -> int:
    maximum = n * (n - 1) // 2
    if k > maximum:
        return 0
    k = min(k, maximum - k)
    modulus = 1_000_000_007
    dp = [0] * (k + 1)
    dp[0] = 1
    for length in range(1, n + 1):
        following = [0] * (k + 1)
        window = 0
        for inversions in range(k + 1):
            window += dp[inversions]
            if inversions >= length:
                window -= dp[inversions - length]
            window %= modulus
            following[inversions] = window
        dp = following
    return dp[k]


class Solution:
    def kInversePairs(self, n: int, k: int) -> int:
        return solve(n, k)
