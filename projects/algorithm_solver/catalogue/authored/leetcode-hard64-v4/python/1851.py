"""1851. Minimum Interval to Include Each Query."""

from heapq import heappop, heappush


def solve(intervals: list[list[int]], queries: list[int]) -> list[int]:
    """Offline query sweep with a minimum-length heap; O((n+q) log(n+q)) time and O(n+q) space. Inputs are preserved."""
    ordered = sorted(intervals)
    answer = [-1] * len(queries)
    available = []
    cursor = 0
    for query, index in sorted((value, index) for index, value in enumerate(queries)):
        while cursor < len(ordered) and ordered[cursor][0] <= query:
            left, right = ordered[cursor]
            heappush(available, (right - left + 1, right))
            cursor += 1
        while available and available[0][1] < query:
            heappop(available)
        if available:
            answer[index] = available[0][0]
    return answer


class Solution:
    def minInterval(self, intervals: list[list[int]], queries: list[int]) -> list[int]:
        return solve(intervals, queries)
