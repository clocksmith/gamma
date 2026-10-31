"""Original frontend 3344 variant; qualification unknown."""


def solve(s: int) -> int:
    def total_sum(n: int) -> int:
        if n <= 1:
            return 0
        i_sum = (n - 1) * n // 2
        or_sum = 0
        for b in range(12):
            period = 1 << (b + 1)
            half = 1 << b
            full = n // period
            rem = n % period
            zeros = full * half + min(rem, half)
            or_sum += (n * n - zeros * zeros) << b
        return i_sum * or_sum

    lo, hi = 1, 1200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if total_sum(mid) <= s:
            lo = mid
        else:
            hi = mid - 1
    return lo


maxSizedArray = solve


class Solution:
    def maxSizedArray(self, s: int) -> int:
        return solve(s)
