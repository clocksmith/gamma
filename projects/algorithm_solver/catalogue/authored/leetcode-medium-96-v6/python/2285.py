"""2285. Maximum Total Importance of Roads: assign the largest labels to vertices with the largest degrees."""


def solve(n: int, roads: list[list[int]]) -> int:
    """O(n log n + e) time and O(n) auxiliary space; inputs are read-only."""
    degree = [0] * n
    for left, right in roads:
        degree[left] += 1
        degree[right] += 1
    degree.sort()
    return sum((index + 1) * count for index, count in enumerate(degree))


class Solution:
    def maximumImportance(self, n: int, roads: list[list[int]]) -> int:
        return solve(n, roads)
