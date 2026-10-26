"""1970. Last Day Where You Can Still Cross."""


def solve(row: int, col: int, cells: list[list[int]]) -> int:
    """Reverse flooding with union-find and virtual borders; O(R*C*alpha(R*C)) time, O(R*C) space. Inputs are preserved."""
    count = row * col
    parent = list(range(count + 2))
    sizes = [1] * (count + 2)
    land = bytearray(count)
    top, bottom = count, count + 1

    def find(node):
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first, second):
        left, right = find(first), find(second)
        if left == right:
            return
        if sizes[left] < sizes[right]:
            left, right = right, left
        parent[right] = left
        sizes[left] += sizes[right]

    for day in range(len(cells) - 1, -1, -1):
        r, c = cells[day][0] - 1, cells[day][1] - 1
        cell = r * col + c
        land[cell] = 1
        if r == 0:
            union(cell, top)
        if r == row - 1:
            union(cell, bottom)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < row and 0 <= nc < col and land[nr * col + nc]:
                union(cell, nr * col + nc)
        if find(top) == find(bottom):
            return day
    return 0


class Solution:
    def latestDayToCross(self, row: int, col: int, cells: list[list[int]]) -> int:
        return solve(row, col, cells)
