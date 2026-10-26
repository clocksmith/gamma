"""3873. Maximum Points Activated with One Addition."""
from __future__ import annotations


def solve(points: list[list[int]]) -> int:
    """O(n alpha(n)) expected time and O(n) space; one new point can connect the two largest coordinate components."""
    n = len(points)
    parent = list(range(n))
    sizes = [1] * n
    def find(node):
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    def union(left, right):
        left, right = find(left), find(right)
        if left == right:
            return
        if sizes[left] < sizes[right]:
            left, right = right, left
        parent[right] = left
        sizes[left] += sizes[right]
    xs, ys = {}, {}
    for index, (x, y) in enumerate(points):
        if x in xs:
            union(index, xs[x])
        else:
            xs[x] = index
        if y in ys:
            union(index, ys[y])
        else:
            ys[y] = index
    largest = second = 0
    for index in range(n):
        if parent[index] != index:
            continue
        size = sizes[index]
        if size >= largest:
            largest, second = size, largest
        elif size > second:
            second = size
    return largest + second + 1


class Solution:
    def maxActivated(self, points: list[list[int]]) -> int:
        return solve(points)
