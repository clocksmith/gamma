"""1377. Frog Position After T Seconds: tree traversal with absorbing leaves; O(n) time and O(n) space."""

from collections import deque


def solve(n: int, edges: list[list[int]], t: int, target: int) -> float:
    neighbors = [[] for _ in range(n + 1)]
    for first, second in edges:
        neighbors[first].append(second)
        neighbors[second].append(first)
    queue = deque([(1, 0, 0, 1.0)])
    while queue:
        node, parent, elapsed, probability = queue.popleft()
        choices = len(neighbors[node]) - int(parent != 0)
        if node == target:
            return probability if elapsed == t or choices == 0 else 0.0
        if elapsed == t or choices == 0:
            continue
        for child in neighbors[node]:
            if child != parent:
                queue.append((child, node, elapsed + 1, probability / choices))
    return 0.0


class Solution:
    def frogPosition(self, n: int, edges: list[list[int]], t: int, target: int) -> float:
        return solve(n, edges, t, target)
