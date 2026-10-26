"""1420. Build Array Where You Can Find The Maximum Exactly K Comparisons: maximum-value DP with prefix sums; O(n*m*k) time and O(m*k) space."""


def solve(n: int, m: int, k: int) -> int:
    modulus = 1_000_000_007
    if k == 0 or k > n or k > m:
        return 0
    previous = [[0] * (m + 1) for _ in range(k + 1)]
    for maximum in range(1, m + 1):
        previous[1][maximum] = 1
    for length in range(2, n + 1):
        current = [[0] * (m + 1) for _ in range(k + 1)]
        for comparisons in range(1, min(k, length) + 1):
            prefix = 0
            for maximum in range(1, m + 1):
                prefix = (prefix + previous[comparisons - 1][maximum - 1]) % modulus
                current[comparisons][maximum] = (previous[comparisons][maximum] * maximum + prefix) % modulus
        previous = current
    return sum(previous[k]) % modulus


class Solution:
    def numOfArrays(self, n: int, m: int, k: int) -> int:
        return solve(n, m, k)
