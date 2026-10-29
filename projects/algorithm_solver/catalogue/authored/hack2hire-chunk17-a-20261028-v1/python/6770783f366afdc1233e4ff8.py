"""Hack2Hire 6770783f366afdc1233e4ff8 (Reduce Gifts) over an INFERRED spec; qualification unknown."""


def solve(prices, k, threshold):
    ordered = sorted(prices)
    n = len(ordered)
    remaining = n
    window = sum(ordered[n - k:n])  # the k largest remaining prices
    while remaining >= k and window > threshold:
        window -= ordered[remaining - 1]
        remaining -= 1
        if remaining >= k:
            window += ordered[remaining - k]
    return n - remaining


class Solution:
    def reduceGifts(self, prices, k, threshold):
        return solve(prices, k, threshold)
