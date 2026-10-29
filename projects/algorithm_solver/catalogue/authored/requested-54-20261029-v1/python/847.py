"""Original development candidate; independent qualification pending."""
from collections import deque

def solve(graph):
    n = len(graph)
    queue = deque((i, 1 << i, 0) for i in range(n))
    seen = {(i, 1 << i) for i in range(n)}
    while queue:
        u,mask,d = queue.popleft()
        if mask == (1 << n)-1:
            return d
        for v in graph[u]:
            state = (v, mask | (1 << v))
            if state not in seen:
                seen.add(state)
                queue.append((*state,d+1))


class Solution:
    def shortestPathLength(self, graph):
        return solve(graph)
