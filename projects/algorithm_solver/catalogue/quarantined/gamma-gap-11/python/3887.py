"""3887. Incremental Even-Weighted Cycle Queries."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]]) -> int:
    """O((n+m) alpha(n)) time and O(n) space; parity union-find accepts only edges consistent with existing path parity."""
    parent = list(range(n))
    sizes = [1] * n
    parity = [0] * n

    def find(node):
        root = node
        total = 0
        while root != parent[root]:
            total ^= parity[root]
            root = parent[root]
        result = total
        while node != root:
            following = parent[node]
            edge = parity[node]
            parent[node] = root
            parity[node] = total
            total ^= edge
            node = following
        return root, result

    answer = 0
    for left, right, weight in edges:
        root_left, value_left = find(left)
        root_right, value_right = find(right)
        relation = value_left ^ value_right ^ weight
        if root_left == root_right:
            if relation == 0:
                answer += 1
            continue
        if sizes[root_left] < sizes[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        parity[root_right] = relation
        sizes[root_left] += sizes[root_right]
        answer += 1
    return answer


class Solution:
    def maxEdges(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
