"""Find eventual safe vertices by removing terminal vertices in reverse."""


def solve(graph: list[list[int]]) -> list[int]:
    """Return ascending safe vertices in O(V + E) time and space; preserve graph."""
    reverse = [[] for _ in graph]
    remaining = [len(neighbors) for neighbors in graph]
    for node, neighbors in enumerate(graph):
        for neighbor in neighbors:
            reverse[neighbor].append(node)
    queue = [node for node, degree in enumerate(remaining) if degree == 0]
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        for predecessor in reverse[node]:
            remaining[predecessor] -= 1
            if remaining[predecessor] == 0:
                queue.append(predecessor)
    return [node for node, degree in enumerate(remaining) if degree == 0]


class Solution:
    def eventualSafeNodes(self, graph: list[list[int]]) -> list[int]:
        return solve(graph)
