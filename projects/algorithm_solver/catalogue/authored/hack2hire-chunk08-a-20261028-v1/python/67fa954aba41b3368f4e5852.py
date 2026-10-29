"""Hack2Hire 67fa954aba41b3368f4e5852 (Random User Pairing, variant 2 of 2) over an INFERRED spec; qualification unknown."""

import heapq


def solve(users):
    members = {}
    for name, group in users:
        members.setdefault(group, []).append(name)
    heap = [(-len(names), group) for group, names in members.items()]
    heapq.heapify(heap)
    taken = dict.fromkeys(members, 0)
    pairs = []
    while len(heap) >= 2:
        count_a, a = heapq.heappop(heap)
        count_b, b = heapq.heappop(heap)
        pairs.append([members[a][taken[a]], members[b][taken[b]]])
        taken[a] += 1
        taken[b] += 1
        if count_a + 1:
            heapq.heappush(heap, (count_a + 1, a))
        if count_b + 1:
            heapq.heappush(heap, (count_b + 1, b))
    return pairs


class Solution:
    def pairAcrossGroups(self, users):
        return solve(users)
