"""3405. Count the Number of Arrays with K Matching Adjacent Elements: choose equal boundaries and color the remaining runs."""


def solve(n: int, m: int, k: int) -> int:
    """O(min(k,n-1-k) + log MOD + log n) time and O(1) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    chosen = min(k, n - 1 - k)
    numerator = denominator = 1
    for index in range(chosen):
        numerator = numerator * (n - 1 - index) % modulus
        denominator = denominator * (index + 1) % modulus
    combinations = numerator * pow(denominator, modulus - 2, modulus) % modulus
    return m * pow(m - 1, n - 1 - k, modulus) % modulus * combinations % modulus


class Solution:
    def countGoodArrays(self, n: int, m: int, k: int) -> int:
        return solve(n, m, k)
