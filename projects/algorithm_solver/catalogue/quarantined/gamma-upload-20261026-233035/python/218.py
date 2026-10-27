"""218. The Skyline Problem."""
import heapq

def solve(buildings: list[list[int]]) -> list[list[int]]:
    events = sorted([(left, -height, right) for left, right, height in buildings] +
                    [(right, 0, 0) for _, right, _ in buildings])
    heap = [(0, float('inf'))]
    result = []
    for x, negative_height, right in events:
        while heap[0][1] <= x:
            heapq.heappop(heap)
        if negative_height:
            heapq.heappush(heap, (negative_height, right))
        height = -heap[0][0]
        if not result or result[-1][1] != height:
            result.append([x, height])
    return result

class Solution:
    def getSkyline(self, buildings: list[list[int]]) -> list[list[int]]:
        return solve(buildings)
