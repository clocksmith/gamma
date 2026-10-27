"""3778. Minimum Distance Excluding One Maximum Weighted Edge
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(n, edges).
Algorithm: Dijkstra on (vertex, free-edge-used), allowing exactly one traversed edge at zero cost.
Complexity: O((n+m) log(n+m)) time; O(n+m) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/minimum-distance-excluding-one-maximum-weighted-edge/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3778.Minimum%20Distance%20Excluding%20One%20Maximum%20Weighted%20Edge/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: For any path, choosing its free edge optimally removes a maximum weight. Ties have the same cost; only the minimum cost is returned. The impl processes the supplied edges without assuming a smaller edge-count bound.
"""

from heapq import heappop, heappush


def solve(n, edges):
    adjacency = [[] for _ in range(n)]
    for first, second, weight in edges:
        adjacency[first].append((second, weight))
        adjacency[second].append((first, weight))
    distances = [[float("inf"), float("inf")] for _ in range(n)]
    distances[0][0] = 0
    pending = [(0, 0, 0)]
    while pending:
        cost, node, used = heappop(pending)
        if cost != distances[node][used]:
            continue
        if node == n - 1 and used:
            return cost
        for neighbor, weight in adjacency[node]:
            paid = cost + weight
            if paid < distances[neighbor][used]:
                distances[neighbor][used] = paid
                heappush(pending, (paid, neighbor, used))
            if not used and cost < distances[neighbor][1]:
                distances[neighbor][1] = cost
                heappush(pending, (cost, neighbor, 1))
    return -1


def minCostExcludingMax(n, edges):
    return solve(n, edges)


class Solution:
    def minCostExcludingMax(self, n, edges):
        return solve(n, edges)
