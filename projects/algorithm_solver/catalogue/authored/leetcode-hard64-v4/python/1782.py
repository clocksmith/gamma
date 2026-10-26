"""1782. Count Pairs Of Nodes."""

from collections import Counter


def solve(n: int, edges: list[list[int]], queries: list[int]) -> list[int]:
    """Sorted degrees with parallel-edge corrections; O(n log n + E + Q*(n+E)) time, O(n+E) space. Inputs are preserved."""
    degree = [0] * n
    shared = Counter()
    for first, second in edges:
        left, right = sorted((first - 1, second - 1))
        degree[left] += 1
        degree[right] += 1
        shared[left, right] += 1
    ordered = sorted(degree)
    answer = []
    for threshold in queries:
        left, right = 0, n - 1
        count = 0
        while left < right:
            if ordered[left] + ordered[right] > threshold:
                count += right - left
                right -= 1
            else:
                left += 1
        for (first, second), overlap in shared.items():
            total = degree[first] + degree[second]
            if total > threshold >= total - overlap:
                count -= 1
        answer.append(count)
    return answer


class Solution:
    def countPairs(self, n: int, edges: list[list[int]], queries: list[int]) -> list[int]:
        return solve(n, edges, queries)
