"""3928. Minimum Cost to Buy Apples II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-cost-to-buy-apples-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3928.Minimum%20Cost%20to%20Buy%20Apples%20II/README_EN.md
Complexity: O(n*(n+m)*log(n+m)) time, O(n+m) auxiliary space.
Outbound and return paths may differ. Distances computed for cost and cost*tax separately, never merged into a single road weight. n<=1000, m<=2000; sums safe in Number. Native name pending.
"""

from __future__ import annotations
from heapq import heappush, heappop

def solve(n, prices, roads):
    graph = [[] for _ in range(n)]
    for first, second, cost, tax in roads:
        graph[first].append((second, cost, cost * tax))
        graph[second].append((first, cost, cost * tax))
    def distances(source, loaded):
        result = [float('inf')] * n
        result[source] = 0
        heap = [(0, source)]
        while heap:
            distance, node = heappop(heap)
            if distance != result[node]:
                continue
            for edge in graph[node]:
                neighbor = edge[0]
                updated = distance + edge[2 if loaded else 1]
                if updated < result[neighbor]:
                    result[neighbor] = updated
                    heappush(heap, (updated, neighbor))
        return result
    answer = []
    for source in range(n):
        outward = distances(source, False)
        inward = distances(source, True)
        answer.append(min(prices[shop] + outward[shop] + inward[shop] for shop in range(n)))
    return answer
