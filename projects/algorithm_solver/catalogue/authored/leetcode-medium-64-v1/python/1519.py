"""1519. Number of Nodes in the Sub-Tree With the Same Label: aggregate label frequencies in an iterative child-before-parent traversal."""
from array import array


def solve(n: int, edges: list[list[int]], labels: str) -> list[int]:
    """O(n) time and O(n) auxiliary space for a fixed 26-letter alphabet; inputs are read-only."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * n
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    counts = array('I', [0]) * (26 * n)
    answer = [0] * n
    for node in reversed(order):
        base = 26 * node
        letter = ord(labels[node]) - ord('a')
        counts[base + letter] += 1
        answer[node] = counts[base + letter]
        if parent[node] != -1:
            target = 26 * parent[node]
            for index in range(26):
                counts[target + index] += counts[base + index]
    return answer


class Solution:
    def countSubTrees(self, n: int, edges: list[list[int]], labels: str) -> list[int]:
        return solve(n, edges, labels)
