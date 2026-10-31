"""Original frontend 3260 variant; qualification unknown."""


def solve(n: int, k: int) -> str:
    m = (n + 1) // 2
    pow10 = [1] * n
    for i in range(1, n):
        pow10[i] = (pow10[i - 1] * 10) % k
    weights = [0] * m
    for i in range(m):
        j = n - 1 - i
        weights[i] = pow10[i] if i == j else (pow10[i] + pow10[j]) % k
    dp = [[False] * k for _ in range(m + 1)]
    dp[m][0] = True
    for i in range(m - 1, -1, -1):
        w = weights[i]
        lo = 1 if i == 0 else 0
        for r in range(k):
            for d in range(9, lo - 1, -1):
                if dp[i + 1][(r + d * w) % k]:
                    dp[i][r] = True
                    break
    res = ["0"] * m
    r = 0
    for i in range(m):
        w = weights[i]
        lo = 1 if i == 0 else 0
        for d in range(9, lo - 1, -1):
            if dp[i + 1][(r + d * w) % k]:
                res[i] = str(d)
                r = (r + d * w) % k
                break
    left = "".join(res)
    right = left[: n // 2][::-1]
    return left + right


largestPalindrome = solve


class Solution:
    def largestPalindrome(self, n: int, k: int) -> str:
        return solve(n, k)
