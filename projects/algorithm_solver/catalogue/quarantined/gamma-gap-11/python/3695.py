"""3695. Maximize Alternating Sum Using Swaps."""
from __future__ import annotations


def solve(nums: list[int], swaps: list[list[int]]) -> int:
    """O(n log n + e * alpha(n)) time and O(n) auxiliary space; caller arrays are preserved."""
    n = len(nums)
    parent = list(range(n))
    size = [1] * n
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    for left, right in swaps:
        left, right = find(left), find(right)
        if left != right:
            if size[left] < size[right]:
                left, right = right, left
            parent[right] = left
            size[left] += size[right]
    groups = {}
    even = {}
    for index, value in enumerate(nums):
        root = find(index)
        groups.setdefault(root, []).append(value)
        even[root] = even.get(root, 0) + (index % 2 == 0)
    answer = 0
    for root, values in groups.items():
        values.sort(reverse=True)
        for index, value in enumerate(values):
            answer += value if index < even[root] else -value
    return answer


class Solution:
    def maxAlternatingSum(self, nums: list[int], swaps: list[list[int]]) -> int:
        return solve(nums, swaps)
