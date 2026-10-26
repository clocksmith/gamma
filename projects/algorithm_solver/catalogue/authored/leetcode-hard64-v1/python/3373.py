"""3373. Maximize the Number of Target Nodes After Connecting Trees II: bipartition parity counts in each tree."""


def solve(edges1: list[list[int]], edges2: list[list[int]]) -> list[int]:
    """O(n + m) time and O(n + m) space. Inputs are preserved."""
    def coloring(edges):
        n = len(edges) + 1
        graph = [[] for _ in range(n)]
        for first, second in edges:
            graph[first].append(second)
            graph[second].append(first)
        colors = [-1] * n
        colors[0] = 0
        counts = [1, 0]
        queue = [0]
        for node in queue:
            for neighbor in graph[node]:
                if colors[neighbor] == -1:
                    colors[neighbor] = colors[node] ^ 1
                    counts[colors[neighbor]] += 1
                    queue.append(neighbor)
        return colors, counts

    colors, counts = coloring(edges1)
    _, other = coloring(edges2)
    # A one-node second tree has no odd-distance node beyond the connecting edge.
    extra = max(other) if edges2 else 0
    return [counts[color] + extra for color in colors]


class Solution:
    def maxTargetNodes(self, edges1: list[list[int]], edges2: list[list[int]]) -> list[int]:
        return solve(edges1, edges2)
