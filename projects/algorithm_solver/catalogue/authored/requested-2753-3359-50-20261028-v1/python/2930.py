"""Original frontend 2930 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(n: int) -> int:
    if n < 4:
        return 0
    p26 = pow(26, n, MOD)
    p25 = pow(25, n - 1, MOD) * (75 + n) % MOD
    p24 = pow(24, n - 1, MOD) * (72 + 2 * n) % MOD
    p23 = pow(23, n - 1, MOD) * (23 + n) % MOD
    return (p26 - p25 + p24 - p23) % MOD


stringCount = solve


class Solution:
    def stringCount(self, n: int) -> int:
        return solve(n)
