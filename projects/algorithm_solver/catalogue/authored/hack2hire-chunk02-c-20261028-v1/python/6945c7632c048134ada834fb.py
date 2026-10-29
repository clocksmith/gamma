"""Hack2Hire 6945c7632c048134ada834fb (Chat Message Range Merge, variant 2) over an INFERRED spec; qualification unknown."""

import heapq


def solve(pages):
    heap = [(page[0][0], number, 0) for number, page in enumerate(pages) if page]
    heapq.heapify(heap)
    result = []
    while heap:
        message_id, number, offset = heapq.heappop(heap)
        if not result or result[-1][0] != message_id:
            result.append([message_id, pages[number][offset][1]])
        if offset + 1 < len(pages[number]):
            heapq.heappush(heap, (pages[number][offset + 1][0], number, offset + 1))
    return result


class Solution:
    def mergePages(self, pages):
        return solve(pages)
