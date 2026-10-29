"""Hack2Hire 685c61e88515b8a3b59d19f9 (Bulk Fruit Order Discount) over an INFERRED spec; qualification unknown."""

from bisect import bisect_right

WINDOW = 600000


def group_cost(quantity, size, unit, thresholds, tiers):
    percent = 0
    if size >= 2:
        i = bisect_right(thresholds, quantity)
        if i:
            percent = tiers[i - 1][1]
    return quantity * unit * (100 - percent) // 100


def solve(orders, prices, tiers):
    price = {}
    for fruit, unit in prices:
        price[fruit] = unit
    by_fruit = {}
    for fruit, quantity, timestamp in orders:
        by_fruit.setdefault(fruit, []).append((int(timestamp), int(quantity)))
    thresholds = [tier[0] for tier in tiers]
    total = 0
    for fruit, items in by_fruit.items():
        items.sort()
        unit = price[fruit]
        quantity = size = 0
        last = None
        for timestamp, amount in items:
            if last is not None and timestamp - last > WINDOW:
                total += group_cost(quantity, size, unit, thresholds, tiers)
                quantity = size = 0
            quantity += amount
            size += 1
            last = timestamp
        total += group_cost(quantity, size, unit, thresholds, tiers)
    return total


class Solution:
    def totalCost(self, orders, prices, tiers):
        return solve(orders, prices, tiers)
