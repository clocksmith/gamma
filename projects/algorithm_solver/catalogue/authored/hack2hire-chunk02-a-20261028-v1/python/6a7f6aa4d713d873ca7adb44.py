"""Hack2Hire 6a7f6aa4d713d873ca7adb44 (Find the Most Common Ads, v1); INFERRED spec; qualification unknown."""
import heapq


class _Key:
    __slots__ = ('count', 'ad')

    def __init__(self, count, ad): self.count, self.ad = count, ad

    def __lt__(self, other):  # heap minimum = weakest entry: lower count, then larger adId
        return self.count < other.count or (self.count == other.count and self.ad > other.ad)


def solve(impressions, k):
    counts = {}
    for _, ad in impressions: counts[ad] = counts.get(ad, 0) + 1
    heap = []
    for ad, count in counts.items():
        key = _Key(count, ad)
        if len(heap) < k: heapq.heappush(heap, key)
        elif heap[0] < key: heapq.heapreplace(heap, key)
    out = []
    while heap: out.append(heapq.heappop(heap).ad)
    return out[::-1]


class Solution:
    def topKAds(self, impressions, k):
        return solve(impressions, k)
