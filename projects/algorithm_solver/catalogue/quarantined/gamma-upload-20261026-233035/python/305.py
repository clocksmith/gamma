"""305. Number of Islands II."""
def solve(m: int, n: int, positions: list[list[int]]) -> list[int]:
    parent = {}
    size = {}
    count = 0
    result = []
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    for row, column in positions:
        node = row * n + column
        if node in parent:
            result.append(count)
            continue
        parent[node] = node
        size[node] = 1
        count += 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            neighbor = nr * n + nc
            if 0 <= nr < m and 0 <= nc < n and neighbor in parent:
                root, other = find(node), find(neighbor)
                if root != other:
                    if size[root] < size[other]:
                        root, other = other, root
                    parent[other] = root
                    size[root] += size[other]
                    count -= 1
        result.append(count)
    return result

class Solution:
    def numIslands2(self, m, n, positions):
        return solve(m, n, positions)
