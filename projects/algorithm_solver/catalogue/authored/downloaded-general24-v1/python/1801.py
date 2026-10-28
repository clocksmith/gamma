"""1801. Number of Orders in the Backlog (Medium).

Specification: https://leetcode.com/problems/number-of-orders-in-the-backlog/description/
"""


import heapq


def solve(orders: list[list[int]]) -> int:
    buy = []
    sell = []
    for price, amount, order_type in orders:
        remaining = amount
        if order_type == 0:
            while remaining > 0 and sell and sell[0][0] <= price:
                top_price, top_amount = heapq.heappop(sell)
                matched = min(remaining, top_amount)
                remaining -= matched
                top_amount -= matched
                if top_amount > 0:
                    heapq.heappush(sell, (top_price, top_amount))
            if remaining > 0:
                heapq.heappush(buy, (-price, remaining))
        else:
            while remaining > 0 and buy and -buy[0][0] >= price:
                top_neg_price, top_amount = heapq.heappop(buy)
                matched = min(remaining, top_amount)
                remaining -= matched
                top_amount -= matched
                if top_amount > 0:
                    heapq.heappush(buy, (top_neg_price, top_amount))
            if remaining > 0:
                heapq.heappush(sell, (price, remaining))
    total = sum(amount for _price, amount in buy) + sum(amount for _price, amount in sell)
    return total % 1000000007


class Solution:
    def getNumberOfBacklogOrders(self, orders: list[list[int]]) -> int:
        return solve(orders)
