"""3004. Maximum Subtree of the Same Color: propagate complete-subtree sizes and color validity in reverse traversal order."""


def solve(edges: list[list[int]], colors: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    adjacency = [[] for _ in colors]
    for left, right in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
    parents = [-1] * len(colors)
    order = [0]
    for node in order:
        for neighbor in adjacency[node]:
            if neighbor != parents[node]:
                parents[neighbor] = node
                order.append(neighbor)
    sizes = [1] * len(colors)
    uniform = [True] * len(colors)
    best = 1
    for node in reversed(order):
        if uniform[node]:
            best = max(best, sizes[node])
        parent = parents[node]
        if parent != -1:
            sizes[parent] += sizes[node]
            if not uniform[node] or colors[node] != colors[parent]:
                uniform[parent] = False
    return best


class Solution:
    def maximumSubtreeSize(self, edges: list[list[int]], colors: list[int]) -> int:
        return solve(edges, colors)
