"""Original frontend 358 variant; qualification unknown."""

from collections import Counter, deque
import heapq


def solve(s: str, k: int) -> str:
    if k <= 1:
        return s
    cnt = Counter(s)
    heap = [(-c, ord(ch), ch) for ch, c in cnt.items()]
    heapq.heapify(heap)
    q = deque()
    res = []
    while heap:
        neg_c, code, ch = heapq.heappop(heap)
        res.append(ch)
        q.append((neg_c + 1, code, ch))
        if len(q) >= k:
            item = q.popleft()
            if item[0] < 0:
                heapq.heappush(heap, item)
    return "".join(res) if len(res) == len(s) else ""


rearrangeString = solve


class Solution:
    def rearrangeString(self, s: str, k: int) -> str:
        return solve(s, k)
