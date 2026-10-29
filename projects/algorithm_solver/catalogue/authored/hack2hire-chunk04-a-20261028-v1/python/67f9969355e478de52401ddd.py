"""Hack2Hire 67f9969355e478de52401ddd (Top Love Message Receivers) over an INFERRED spec; qualification unknown."""

from heapq import heapify, heappop


def solve(messages, k):
    pairs, count = set(), {}
    for sender, receiver, _ in messages:
        if (sender, receiver) not in pairs:
            pairs.add((sender, receiver))
            count[receiver] = count.get(receiver, 0) + 1
    heap = [(-c, name) for name, c in count.items()]
    heapify(heap)
    return [heappop(heap)[1] for _ in range(min(k, len(heap)))]


class Solution:
    def topReceivers(self, messages, k):
        return solve(messages, k)
