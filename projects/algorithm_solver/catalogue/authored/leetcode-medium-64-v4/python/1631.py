"""1631. Path With Minimum Effort: join grid edges by increasing effort until the corners become connected."""


def solve(heights: list[list[int]]) -> int:
    """O(r * c * log(r * c + 1)) time and O(r * c) auxiliary space; inputs are read-only."""
    rows, cols = len(heights), len(heights[0])
    count = rows * cols
    if count == 1:
        return 0
    edges = []
    for row in range(rows):
        for col in range(cols):
            node = row * cols + col
            if row + 1 < rows:
                edges.append((abs(heights[row][col] - heights[row + 1][col]), node, node + cols))
            if col + 1 < cols:
                edges.append((abs(heights[row][col] - heights[row][col + 1]), node, node + 1))
    edges.sort()
    parent = list(range(count))
    size = [1] * count

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for effort, first, second in edges:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            if size[first_root] < size[second_root]:
                first_root, second_root = second_root, first_root
            parent[second_root] = first_root
            size[first_root] += size[second_root]
        if find(0) == find(count - 1):
            return effort
    return 0


class Solution:
    def minimumEffortPath(self, heights: list[list[int]]) -> int:
        return solve(heights)
