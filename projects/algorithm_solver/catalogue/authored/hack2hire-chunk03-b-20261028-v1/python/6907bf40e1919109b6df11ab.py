"""Hack2Hire 6907bf40e1919109b6df11ab (Merge K Sorted Price Streams) over an INFERRED spec; qualification unknown."""
import heapq


def parse(event):
    t, d = event.split(', ')
    return int(t), int(d)


def solve(streams):
    heap = [(parse(s[0])[0], i, 0) for i, s in enumerate(streams) if s]
    heapq.heapify(heap)
    result, price = [], 0
    while heap:
        t = heap[0][0]
        while heap and heap[0][0] == t:
            _, i, j = heapq.heappop(heap)
            price += parse(streams[i][j])[1]
            if j + 1 < len(streams[i]): heapq.heappush(heap, (parse(streams[i][j + 1])[0], i, j + 1))
        result.append(f'{t}, {price}')
    return result


class Solution:
    def mergePriceStreams(self, streams):
        return solve(streams)
