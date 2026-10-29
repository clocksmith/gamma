"""Hack2Hire 696aacf2cc483345efb1b29f (Minimum Expected Asset Cost) over an INFERRED spec; qualification unknown."""

def solve(n, k, a, b, p):
    m = b - a + 1
    top = min(k, n)
    price_sum = (a + b) * m // 2
    prev = [0] * (top + 1)  # numerators over m ** (i - 1)
    scale = 1
    for _ in range(n):
        cur = [0] * (top + 1)
        cur[0] = m * prev[0] + scale * price_sum
        for j in range(1, top + 1):
            keep = prev[j]
            fixed = p * scale + prev[j - 1]
            hi = min(b, (fixed - keep) // scale)  # market price wins while x * scale + keep <= fixed
            if hi < a:
                cur[j] = m * fixed
            else:
                cnt = hi - a + 1
                cur[j] = scale * ((a + hi) * cnt // 2) + keep * cnt + (m - cnt) * fixed
        prev = cur
        scale *= m
    q = (2 * prev[top] * 10 ** 6 + scale) // (2 * scale)
    return '%d.%06d' % (q // 10 ** 6, q % 10 ** 6)


class Solution:
    def minExpectedCost(self, n, k, a, b, p):
        return solve(n, k, a, b, p)
