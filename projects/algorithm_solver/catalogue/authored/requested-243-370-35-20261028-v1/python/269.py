"""Original frontend 269 variant; qualification unknown."""

import heapq


def solve(words) -> str:
    chars = sorted({ch for w in words for ch in w})
    adj = {c: set() for c in chars}
    indeg = {c: 0 for c in chars}
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if len(w1) > len(w2) and w1.startswith(w2):
            return ""
        for a, b in zip(w1, w2):
            if a != b:
                if b not in adj[a]:
                    adj[a].add(b)
                    indeg[b] += 1
                break
    heap = [c for c in chars if indeg[c] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        u = heapq.heappop(heap)
        out.append(u)
        for v in sorted(adj[u]):
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, v)
    return "".join(out) if len(out) == len(chars) else ""


alienOrder = solve


class Solution:
    def alienOrder(self, words) -> str:
        return solve(words)
