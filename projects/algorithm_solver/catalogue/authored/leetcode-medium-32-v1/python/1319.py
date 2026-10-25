"""1319. Number of Operations to Make Network Connected: merge components with union by size and path halving."""


def solve(n: int, connections: list[list[int]]) -> int:
    """O(n + e * alpha(n)) time and O(n) auxiliary space; inputs are read-only."""
    if len(connections) < n - 1:
        return -1
    parent = list(range(n))
    size = [1] * n
    components = n

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for left, right in connections:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            continue
        if size[left_root] < size[right_root]:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        size[left_root] += size[right_root]
        components -= 1
    return components - 1


class Solution:
    def makeConnected(self, n: int, connections: list[list[int]]) -> int:
        return solve(n, connections)
