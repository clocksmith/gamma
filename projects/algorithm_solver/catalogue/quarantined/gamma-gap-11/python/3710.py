"""3710. Maximum Partition Factor."""
from __future__ import annotations


def solve(points: list[list[int]]) -> int:
    """O(n^2 log n) time and O(n^2) space; the first odd-cycle threshold bounds two-color separation."""
    n = len(points)
    if n == 2:
        return 0
    edges = []
    for left in range(n):
        for right in range(left + 1, n):
            distance = abs(points[left][0] - points[right][0]) + abs(points[left][1] - points[right][1])
            edges.append((distance, left, right))
    edges.sort()
    parent = list(range(2 * n))
    size = [1] * (2 * n)
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    def unite(left, right):
        left, right = find(left), find(right)
        if left == right:
            return
        if size[left] < size[right]:
            left, right = right, left
        parent[right] = left
        size[left] += size[right]
    for distance, left, right in edges:
        if find(left) == find(right):
            return distance
        unite(left, right + n)
        unite(right, left + n)
    return 0


class Solution:
    def maxPartitionFactor(self, points: list[list[int]]) -> int:
        return solve(points)
