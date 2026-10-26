"""1857. Largest Color Value in a Directed Graph."""

from collections import deque


def solve(colors: str, edges: list[list[int]]) -> int:
    """Topological color-count DP and explicit cycle detection; O(26*(V+E)) time and O(26*V+E) space. Inputs are preserved."""
    size = len(colors)
    neighbors = [[] for _ in range(size)]
    incoming = [0] * size
    for source, target in edges:
        neighbors[source].append(target)
        incoming[target] += 1
    queue = deque(node for node in range(size) if incoming[node] == 0)
    counts = [[0] * 26 for _ in range(size)]
    processed = 0
    answer = 0
    while queue:
        node = queue.popleft()
        processed += 1
        counts[node][ord(colors[node]) - ord('a')] += 1
        answer = max(answer, max(counts[node]))
        for target in neighbors[node]:
            for color in range(26):
                counts[target][color] = max(counts[target][color], counts[node][color])
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    return answer if processed == size else -1


class Solution:
    def largestPathValue(self, colors: str, edges: list[list[int]]) -> int:
        return solve(colors, edges)
