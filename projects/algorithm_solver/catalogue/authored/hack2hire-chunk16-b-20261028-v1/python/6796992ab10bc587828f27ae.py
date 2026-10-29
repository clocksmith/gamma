"""Hack2Hire 6796992ab10bc587828f27ae (Minimize Capital Gains Tax) over an INFERRED spec; qualification unknown."""

import heapq


def solve(transactions):
    heap = []  # (-price, remaining amount)
    tenths = 0
    for _, kind, amount, price in transactions:
        need = int(amount)
        p = int(price)
        if kind == 'buy':
            heapq.heappush(heap, (-p, need))
            continue
        profit = 0
        while need:
            negative, have = heap[0]
            take = need if need < have else have
            profit += (p + negative) * take
            need -= take
            if take == have:
                heapq.heappop(heap)
            else:
                heapq.heapreplace(heap, (negative, have - take))
        if profit > 0:
            tenths += profit
    return str(tenths // 10) + '.' + str(tenths % 10)


class Solution:
    def minimizeTax(self, transactions):
        return solve(transactions)
