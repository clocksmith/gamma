"""2101. Detonate the Maximum Bombs: build directed radius reachability and explore every possible first detonation."""


def solve(bombs: list[list[int]]) -> int:
    """O(n^3) time and O(n^2) auxiliary space; inputs are read-only."""
    size = len(bombs)
    graph = [[] for _ in bombs]
    for left, (x, y, radius) in enumerate(bombs):
        for right, (other_x, other_y, _) in enumerate(bombs):
            if left != right and (x - other_x) ** 2 + (y - other_y) ** 2 <= radius * radius:
                graph[left].append(right)
    best = 0
    for start in range(size):
        seen = {start}
        stack = [start]
        while stack:
            for neighbor in graph[stack.pop()]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        best = max(best, len(seen))
        if best == size:
            break
    return best


class Solution:
    def maximumDetonation(self, bombs: list[list[int]]) -> int:
        return solve(bombs)
