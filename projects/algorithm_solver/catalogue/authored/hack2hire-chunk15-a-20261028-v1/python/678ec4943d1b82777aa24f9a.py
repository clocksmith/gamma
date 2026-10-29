"""Hack2Hire 678ec4943d1b82777aa24f9a (Crypto Order Matching) over an INFERRED spec; qualification unknown."""

import heapq


def solve(buyPrices, sellPrices, orders):
    buys = [-price for price in buyPrices]
    heapq.heapify(buys)
    sells = list(sellPrices)
    heapq.heapify(sells)
    result = []
    for side, price in orders:
        if side == 'buy':
            if sells and sells[0] <= price:
                result.append(heapq.heappop(sells))
            else:
                heapq.heappush(buys, -price)
                result.append(-1)
        else:
            if buys and -buys[0] >= price:
                result.append(-heapq.heappop(buys))
            else:
                heapq.heappush(sells, price)
                result.append(-1)
    return result


class Solution:
    def matchOrders(self, buyPrices, sellPrices, orders):
        return solve(buyPrices, sellPrices, orders)
