"""3787. Find Diameter Endpoints of a Tree
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(n, edges).
Algorithm: Three breadth-first searches; a vertex is a diameter endpoint iff its distance to either fixed diameter endpoint equals the diameter.
Complexity: O(n) time and space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/find-diameter-endpoints-of-a-tree/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3787.Find%20Diameter%20Endpoints%20of%20a%20Tree/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Returns a binary string, not just one pair of diameter endpoints.
"""

def solve(n, edges):
    adjacency = [[] for _ in range(n)]
    for first, second in edges:
        adjacency[first].append(second)
        adjacency[second].append(first)

    def distances_from(start):
        distances = [-1] * n
        distances[start] = 0
        queue = [start]
        for node in queue:
            for neighbor in adjacency[node]:
                if distances[neighbor] == -1:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)
        return queue[-1], distances

    first, _ = distances_from(0)
    second, from_first = distances_from(first)
    _, from_second = distances_from(second)
    diameter = from_first[second]
    return "".join("1" if from_first[node] == diameter or from_second[node] == diameter else "0"
                   for node in range(n))


def findSpecialNodes(n, edges):
    return solve(n, edges)


class Solution:
    def findSpecialNodes(self, n, edges):
        return solve(n, edges)
