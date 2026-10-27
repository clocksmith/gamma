"""3807. Minimum Cost to Repair Edges to Traverse a Graph
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(n, edges, k).
Algorithm: Binary search the repair threshold; bounded breadth-first search checks at most k edges.
Complexity: O(m log m + (n+m) log m) time; O(n+m) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/minimum-cost-to-repair-edges-to-traverse-a-graph/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3807.Minimum%20Cost%20to%20Repair%20Edges%20to%20Traverse%20a%20Graph/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: money is a threshold for repairing all affordable edges, not their summed repair costs.
"""

def solve(n, edges, k):
    adjacency = [[] for _ in range(n)]
    for first, second, cost in edges:
        adjacency[first].append((second, cost))
        adjacency[second].append((first, cost))
    costs = sorted({edge[2] for edge in edges})

    def reachable(budget):
        distance = [-1] * n
        distance[0] = 0
        queue = [0]
        for node in queue:
            if node == n - 1:
                return True
            if distance[node] == k:
                continue
            for neighbor, cost in adjacency[node]:
                if cost <= budget and distance[neighbor] == -1:
                    distance[neighbor] = distance[node] + 1
                    queue.append(neighbor)
        return False

    if not costs or not reachable(costs[-1]):
        return -1
    left, right = 0, len(costs) - 1
    while left < right:
        middle = (left + right) // 2
        if reachable(costs[middle]):
            right = middle
        else:
            left = middle + 1
    return costs[left]


def minCost(n, edges, k):
    return solve(n, edges, k)


class Solution:
    def minCost(self, n, edges, k):
        return solve(n, edges, k)
