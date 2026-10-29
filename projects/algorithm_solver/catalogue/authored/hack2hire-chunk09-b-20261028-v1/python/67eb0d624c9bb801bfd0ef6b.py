"""Hack2Hire 67eb0d624c9bb801bfd0ef6b (Candlestick Data Generator) over an INFERRED spec; qualification unknown."""


def solve(prices):
    ordered = sorted(prices, key=lambda pair: pair[0])
    out = []
    current = None
    for time, price in ordered:
        start = time - time % 10
        if current is None or current[0] != start:
            current = [start, price, price, price, price]
            out.append(current)
        else:
            if price > current[1]:
                current[1] = price
            if price < current[2]:
                current[2] = price
            current[4] = price
    return out


class Solution:
    def generateCandlesticks(self, prices):
        return solve(prices)
