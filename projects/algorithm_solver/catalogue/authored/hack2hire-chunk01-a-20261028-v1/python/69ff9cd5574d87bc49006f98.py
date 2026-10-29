"""Hack2Hire 69ff9cd5574d87bc49006f98 (Card Packets with Identical Distribution) over an INFERRED spec; qualification unknown."""


def solve(cardTypes):
    limit = max(max(cardTypes), 2)
    count = [0] * (limit + 1)
    total = [0] * (limit + 1)
    for value in cardTypes:
        count[value] += 1
        total[value] += value
    for v in range(1, limit + 1):
        count[v] += count[v - 1]
        total[v] += total[v - 1]
    composite = bytearray(limit + 1)
    best = None
    for p in range(2, limit + 1):
        if composite[p]:
            continue
        for multiple in range(p * p, limit + 1, p):
            composite[multiple] = 1
        cost, low = 0, 0  # block (low, high] rounds every value up to high
        while low < limit:
            high = min(low + p, limit)
            target = low + p
            cost += (count[high] - count[low]) * target - (total[high] - total[low])
            low = high
        if best is None or cost < best:
            best = cost
    return best


class Solution:
    def minAdditionalCards(self, cardTypes):
        return solve(cardTypes)
