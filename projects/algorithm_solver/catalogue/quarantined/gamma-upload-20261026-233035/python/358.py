"""358. Rearrange String k Distance Apart."""
import heapq
from collections import Counter, deque

def solve(s: str, k: int) -> str:
    if k <= 1:
        return s
    heap = [(-count, char) for char, count in Counter(s).items()]
    heapq.heapify(heap)
    waiting = deque()
    result = []
    while heap:
        count, char = heapq.heappop(heap)
        result.append(char)
        waiting.append((count + 1, char))
        if len(waiting) >= k:
            old_count, old_char = waiting.popleft()
            if old_count < 0:
                heapq.heappush(heap, (old_count, old_char))
    return ''.join(result) if len(result) == len(s) else ''

class Solution:
    def rearrangeString(self, s: str, k: int) -> str:
        return solve(s, k)
