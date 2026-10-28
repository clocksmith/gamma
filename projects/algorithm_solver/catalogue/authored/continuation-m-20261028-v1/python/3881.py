def solve(n, pos, k):
    mod = 1000000007
    k = min(k, n - 1 - k)
    numerator = denominator = 1
    for i in range(1, k + 1):
        numerator = numerator * (n - i) % mod
        denominator = denominator * i % mod
    return 2 * numerator * pow(denominator, mod - 2, mod) % mod


class Solution:
    def countVisiblePeople(self, n, pos, k):
        return solve(n, pos, k)
