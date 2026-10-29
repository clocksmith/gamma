"""Hack2Hire 67a4d4ca2a9ed767fa215433 (Maximize Negative Signs) over an INFERRED spec; qualification unknown."""

import heapq


def solve(a):
    total = 0
    negated = []
    for value in a:
        total -= value
        heapq.heappush(negated, -value)
        while total <= 0:
            total += 2 * -heapq.heappop(negated)
    return len(negated)


class Solution:
    def maximizeNegativeSigns(self, a):
        return solve(a)
