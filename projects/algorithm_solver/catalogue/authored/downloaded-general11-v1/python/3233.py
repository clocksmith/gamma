"""3233. Find the Count of Numbers Which Are Not Special (Medium).

Specification: https://leetcode.com/problems/find-the-count-of-numbers-which-are-not-special/description/
"""


def solve(l: int, r: int) -> int:
    import math
    limit = math.isqrt(r)
    is_prime = [True] * (limit + 1)
    if limit >= 0:
        is_prime[0] = False
    if limit >= 1:
        is_prime[1] = False
    i = 2
    while i * i <= limit:
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
        i += 1
    cnt = 0
    for p in range(2, limit + 1):
        if is_prime[p] and l <= p * p <= r:
            cnt += 1
    return (r - l + 1) - cnt


class Solution:
    def nonSpecialCount(self, l, r):
        return solve(l, r)
