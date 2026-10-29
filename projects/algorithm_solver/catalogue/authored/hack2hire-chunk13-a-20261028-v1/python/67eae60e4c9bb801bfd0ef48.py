"""Hack2Hire 67eae60e4c9bb801bfd0ef48 (Rearrange Houses in Neighborhoods) over an INFERRED spec; qualification unknown."""
import heapq


def solve(houses):
    copies = {}
    for row in houses:
        for v in row:
            copies[v] = copies.get(v, 0) + 1
    heap = [(-c, v) for v, c in copies.items()]  # most copies first, smaller number on ties
    heapq.heapify(heap)
    out = []
    for row in houses:
        need = len(row)
        if need > len(heap):
            return []
        taken = [heapq.heappop(heap) for _ in range(need)]
        out.append(sorted(v for _, v in taken))
        for c, v in taken:
            if c < -1:
                heapq.heappush(heap, (c + 1, v))
    return out


class Solution:
    def rearrangeHouses(self, houses):
        return solve(houses)
