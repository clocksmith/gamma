"""Hack2Hire 67f5703f83ba2e5f057e6dfb (Prefix Search I) over an INFERRED spec; qualification unknown."""

import heapq


def solve(bizNames, prefix, k):
    p = prefix.lower()
    width = len(p)
    keyed = []
    for name in bizNames:
        for position, word in enumerate(name.split(' ')):
            if word[:width].lower() == p:
                keyed.append((position, name))
                break
    return [name for _, name in heapq.nsmallest(k, keyed)]


class Solution:
    def topKBusinessNames(self, bizNames, prefix, k):
        return solve(bizNames, prefix, k)
