"""Hack2Hire 68f012a4742c37be9dc830dd (Build Binary Tree From Character Counts) over an INFERRED spec; qualification unknown."""
import heapq


def solve(s):
    if not s:
        return None
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    heap = []
    next_id = 0
    for ch in sorted(counts):
        heap.append((counts[ch], next_id, {'ch': ch, 'count': counts[ch], 'left': None, 'right': None}))
        next_id += 1
    heapq.heapify(heap)
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        total = a[0] + b[0]
        heapq.heappush(heap, (total, next_id, {'ch': '#', 'count': total, 'left': a[2], 'right': b[2]}))
        next_id += 1
    return heap[0][2]


class Solution:
    def buildTree(self, s):
        return solve(s)
