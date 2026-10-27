"""323. Number of Connected Components in an Undirected Graph."""
def solve(n: int, edges: list[list[int]]) -> int:
    parent = list(range(n))
    count = n
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    for left, right in edges:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_left] = root_right
            count -= 1
    return count

class Solution:
    def countComponents(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
