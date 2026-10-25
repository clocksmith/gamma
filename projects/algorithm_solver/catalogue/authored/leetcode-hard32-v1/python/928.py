"""928. Minimize Malware Spread II."""

def solve(graph: list[list[int]], initial: list[int]) -> int:
    """O(n^2) time, O(n) space; save clean components touched by one infected node."""
    size = len(graph)
    infected = set(initial)
    visited = [False] * size
    saved = [0] * size
    for start in range(size):
        if start in infected or visited[start]:
            continue
        stack = [start]
        visited[start] = True
        count = 0
        sources = set()
        while stack:
            node = stack.pop()
            count += 1
            for neighbor, connected in enumerate(graph[node]):
                if not connected:
                    continue
                if neighbor in infected:
                    sources.add(neighbor)
                elif not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)
        if len(sources) == 1:
            saved[next(iter(sources))] += count
    return min(initial, key=lambda node: (-saved[node], node))


class Solution:
    def minMalwareSpread(self, graph: list[list[int]], initial: list[int]) -> int:
        return solve(graph, initial)
