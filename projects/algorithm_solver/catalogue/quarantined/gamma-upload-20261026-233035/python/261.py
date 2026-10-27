"""261. Graph Valid Tree."""
def solve(n: int, edges: list[list[int]]) -> bool:
    if len(edges) != n - 1:
        return False
    parent = list(range(n))
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    for left, right in edges:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            return False
        parent[root_left] = root_right
    return True

class Solution:
    def validTree(self, n: int, edges: list[list[int]]) -> bool:
        return solve(n, edges)
