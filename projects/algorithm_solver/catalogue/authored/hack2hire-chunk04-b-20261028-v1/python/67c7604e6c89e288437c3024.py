"""Hack2Hire 67c7604e6c89e288437c3024 (Cake Order Fulfillment Check) over an INFERRED spec; qualification unknown."""


def solve(stock, orders):
    a, b, c = stock
    result = []
    for x, y, z in orders:
        ok = x <= a and y <= b and z <= c
        if ok:
            a -= x
            b -= y
            c -= z
        result.append(ok)
    return result


class Solution:
    def checkOrders(self, stock, orders):
        return solve(stock, orders)
