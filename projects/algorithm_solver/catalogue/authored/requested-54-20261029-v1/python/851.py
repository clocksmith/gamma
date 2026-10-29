"""Original development candidate; independent qualification pending."""
from collections import deque

def solve(richer, quiet):
    n = len(quiet)
    edges = [[] for _ in range(n)]
    indegree = [0]*n
    answer = list(range(n))
    for a,b in richer:
        edges[a].append(b)
        indegree[b] += 1
    queue = deque(i for i in range(n) if not indegree[i])
    while queue:
        a = queue.popleft()
        for b in edges[a]:
            if quiet[answer[a]] < quiet[answer[b]]:
                answer[b] = answer[a]
            indegree[b] -= 1
            if not indegree[b]:
                queue.append(b)
    return answer


class Solution:
    def loudAndRich(self, richer, quiet):
        return solve(richer, quiet)
