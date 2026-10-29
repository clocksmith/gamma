"""Hack2Hire 68b82be483188776facc8f08 (Minimum Menu Order Cost I, level 1) over an INFERRED spec; qualification unknown."""

LEVEL = 1


def solve(menu, userWants):
    index = {x: i for i, x in enumerate(userWants)}
    full = (1 << len(userWants)) - 1
    cheapest = {}
    for _entry_id, price, items in menu:
        mask = 0
        for x in items.split(','):
            if x in index:
                mask |= 1 << index[x]
        if mask and (mask not in cheapest or price < cheapest[mask]):
            cheapest[mask] = price
    entries = list(cheapest.items())
    cost = [None] * (full + 1)
    count = [0] * (full + 1)
    cost[0] = 0
    for mask in range(full + 1):
        c = cost[mask]
        if c is None:
            continue
        for e, price in entries:
            nm = mask | e
            if nm == mask:
                continue
            nc, nk = c + price, count[mask] + 1
            if cost[nm] is None or nc < cost[nm] or (nc == cost[nm] and nk < count[nm]):
                cost[nm], count[nm] = nc, nk
    if LEVEL == 1:
        return -1 if cost[full] is None else cost[full]
    return [-1, -1] if cost[full] is None else [cost[full], count[full]]


class Solution:
    def minOrderCost(self, menu, userWants):
        return solve(menu, userWants)
