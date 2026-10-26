"""2876. Count Visited Nodes in a Directed Graph. Peel directed tails, measure remaining cycles, then restore tail lengths."""


def solve(edges: list[int]) -> list[int]:
    """O(n) time and O(n) space. Inputs are preserved."""
    size = len(edges)
    indegree = [0] * size
    for neighbor in edges:
        indegree[neighbor] += 1
    order = [node for node in range(size) if indegree[node] == 0]
    for node in order:
        neighbor = edges[node]
        indegree[neighbor] -= 1
        if indegree[neighbor] == 0:
            order.append(neighbor)
    answer = [0] * size
    for start in range(size):
        if indegree[start] == 0:
            continue
        cycle = []
        node = start
        while indegree[node] > 0:
            cycle.append(node)
            indegree[node] = 0
            node = edges[node]
        for node in cycle:
            answer[node] = len(cycle)
    for node in reversed(order):
        answer[node] = answer[edges[node]] + 1
    return answer


class Solution:
    def countVisitedNodes(self, edges: list[int]) -> list[int]:
        return solve(edges)
