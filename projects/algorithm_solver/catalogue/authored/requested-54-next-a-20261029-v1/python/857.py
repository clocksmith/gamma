"""Original development candidate; qualification unknown."""
from functools import cmp_to_key
import heapq

def solve(quality, wage, k):
    workers = list(zip(quality,wage))
    workers.sort(key=cmp_to_key(lambda a,b: a[1]*b[0]-b[1]*a[0]))
    heap = []
    total = 0
    answer = float('inf')
    for q,w in workers:
        total += q
        heapq.heappush(heap,-q)
        if len(heap) > k:
            total += heapq.heappop(heap)
        if len(heap) == k:
            answer = min(answer,total*w/q)
    return answer


class Solution:
    def mincostToHireWorkers(self, quality, wage, k):
        return solve(quality, wage, k)
