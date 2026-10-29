"""Hack2Hire 67a56d81b571d6ff0a4bd238 (Bring Servers Down) over an INFERRED spec; qualification unknown."""

from functools import cmp_to_key


def solve(request, health, k):
    hits = [(h + k - 1) // k for h in health]

    def before(i, j):
        return hits[i] * request[j] - hits[j] * request[i]
    order = sorted(range(len(request)), key=cmp_to_key(before))
    total = 0
    elapsed = 0
    for i in order:
        elapsed += hits[i]
        total += request[i] * elapsed
    return total


class Solution:
    def getMinRequests(self, request, health, k):
        return solve(request, health, k)
