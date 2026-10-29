"""Hack2Hire 67843d1e0e1dbb6a0938577d (Find Eligible Order Sequence) over an INFERRED spec; qualification unknown."""

import heapq


def solve(orderIds):
    a = orderIds
    n = len(a)
    prev = list(range(-1, n - 1))
    nxt = list(range(1, n + 1))
    queued = [False] * n

    def eligible(i):
        return (prev[i] < 0 or a[i] > a[prev[i]]) and (nxt[i] >= n or a[i] > a[nxt[i]])

    heap = []
    for i in range(n):
        if eligible(i):
            queued[i] = True
            heap.append((a[i], i))
    heapq.heapify(heap)
    out = []
    while heap:
        value, i = heapq.heappop(heap)
        out.append(value)
        p, q = prev[i], nxt[i]
        if p >= 0:
            nxt[p] = q
        if q < n:
            prev[q] = p
        for j in (p, q):
            if 0 <= j < n and not queued[j] and eligible(j):
                queued[j] = True
                heapq.heappush(heap, (a[j], j))
    return out


class Solution:
    def eligibleOrderSequence(self, orderIds):
        return solve(orderIds)
