"""2316. Count Unreachable Pairs of Nodes in an Undirected Graph: join components and count pairs between each component and the uncounted remainder."""


def solve(n: int, edges: list[list[int]]) -> int:
    """O(n + e * alpha(n)) time and O(n) auxiliary space; inputs are read-only."""
    parent = list(range(n))
    size = [1] * n

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for left, right in edges:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            continue
        if size[left_root] < size[right_root]:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        size[left_root] += size[right_root]
    remaining = n
    answer = 0
    for node in range(n):
        if parent[node] == node:
            remaining -= size[node]
            answer += size[node] * remaining
    return answer


class Solution:
    def countPairs(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
