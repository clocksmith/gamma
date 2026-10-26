"""2911. Minimum Changes to Make K Semi-palindromes.

Precompute every proper-divisor palindrome cost, then partition prefixes; O(n^3 log n + k*n^2) time, O(n^2) space.
"""

def solve(s: str, k: int) -> int:
    n = len(s)
    divisors = [[] for _ in range(n + 1)]
    for step in range(1, n // 2 + 1):
        for length in range(2 * step, n + 1, step):
            divisors[length].append(step)
    cost = [[n] * n for _ in range(n)]
    for start in range(n):
        for length in range(2, n - start + 1):
            best = n
            for step in divisors[length]:
                edits = 0
                for offset in range(step):
                    left, right = start + offset, start + length - step + offset
                    while left < right:
                        edits += s[left] != s[right]
                        left += step
                        right -= step
                best = min(best, edits)
            cost[start][start + length - 1] = best
    dp = [0] + [n] * n
    for parts in range(1, k + 1):
        following = [n] * (n + 1)
        for end in range(2 * parts, n + 1):
            following[end] = min(dp[start] + cost[start][end - 1] for start in range(2 * (parts - 1), end - 1))
        dp = following
    return dp[n]


class Solution:
    def minimumChanges(self, s: str, k: int) -> int:
        return solve(s, k)
