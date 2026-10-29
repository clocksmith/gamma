"""Hack2Hire 67e8af3a7131f7c901ffd7a1 (Find Maximum Trade Shares). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""
import heapq


def solve(orders):
    sells, buys, remaining, traded = [], [], [], 0
    for price, quantity, kind in orders:
        if kind == 'buy':
            book, crosses, own, key = sells, (lambda top: top <= price), buys, -price
        else:
            book, crosses, own, key = buys, (lambda top: -top >= price), sells, price
        while quantity and book and crosses(book[0][0]):
            index = book[0][1]
            take = min(quantity, remaining[index])
            traded += take
            quantity -= take
            remaining[index] -= take
            if remaining[index] == 0:
                heapq.heappop(book)
        if quantity:
            remaining.append(quantity)
            heapq.heappush(own, (key, len(remaining) - 1))
    return traded


class Solution:
    def maxTradedShares(self, orders):
        return solve(orders)
