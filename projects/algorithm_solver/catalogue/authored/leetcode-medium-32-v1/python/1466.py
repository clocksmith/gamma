"""1466. Reorder Routes to Make All Paths Lead to the City Zero: traverse the tree and count edges pointing away from zero."""


def solve(n: int, connections: list[list[int]]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    graph = [[] for _ in range(n)]
    for start, end in connections:
        graph[start].append((end, 1))
        graph[end].append((start, 0))
    stack = [(0, -1)]
    answer = 0
    while stack:
        node, parent = stack.pop()
        for neighbor, reversal in graph[node]:
            if neighbor == parent:
                continue
            answer += reversal
            stack.append((neighbor, node))
    return answer


class Solution:
    def minReorder(self, n: int, connections: list[list[int]]) -> int:
        return solve(n, connections)
