"""1443. Minimum Time to Collect All Apples in a Tree: propagate apple requirements toward the root in reverse traversal order."""


def solve(n: int, edges: list[list[int]], hasApple: list[bool]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = [-1] * n
    order = [0]
    for node in order:
        for child in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    needed = hasApple.copy()
    total = 0
    for index in range(n - 1, 0, -1):
        node = order[index]
        if needed[node]:
            total += 2
            needed[parent[node]] = True
    return total


class Solution:
    def minTime(self, n: int, edges: list[list[int]], hasApple: list[bool]) -> int:
        return solve(n, edges, hasApple)
