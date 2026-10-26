"""2368. Reachable Nodes With Restrictions: traverse the allowed component from zero without recursive depth limits."""


def solve(n: int, edges: list[list[int]], restricted: list[int]) -> int:
    """O(n + e) time and O(n + e) auxiliary space; inputs are read-only."""
    blocked = set(restricted)
    if 0 in blocked:
        return 0
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    seen = {0}
    stack = [0]
    while stack:
        node = stack.pop()
        for neighbor in graph[node]:
            if neighbor not in blocked and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen)


class Solution:
    def reachableNodes(self, n: int, edges: list[list[int]], restricted: list[int]) -> int:
        return solve(n, edges, restricted)
