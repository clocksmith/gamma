"""Original frontend 3339 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(n: int, m: int, k: int) -> int:
    even = m // 2
    odd = m - even
    dp0 = [0] * (k + 1)
    dp1 = [0] * (k + 1)
    dp0[0] = even
    dp1[0] = odd
    for _ in range(1, n):
        ndp0 = [0] * (k + 1)
        ndp1 = [0] * (k + 1)
        for c in range(k + 1):
            ways_any = (dp0[c] + dp1[c]) % MOD
            ndp1[c] = (ways_any * odd) % MOD
            ndp0[c] = (dp1[c] * even) % MOD
            if c > 0:
                ndp0[c] = (ndp0[c] + dp0[c - 1] * even) % MOD
        dp0, dp1 = ndp0, ndp1
    return (dp0[k] + dp1[k]) % MOD


countOfArrays = solve


class Solution:
    def countOfArrays(self, n: int, m: int, k: int) -> int:
        return solve(n, m, k)
