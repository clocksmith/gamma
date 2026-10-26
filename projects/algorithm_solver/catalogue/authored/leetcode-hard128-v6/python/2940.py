"""2940. Find Building Where Alice and Bob Can Meet.

Activate unresolved queries at their right endpoint and discharge by height; O(n + q log q) time, O(n+q) space. Inputs are preserved.
"""

from heapq import heappop, heappush


def solve(heights: list[int], queries: list[list[int]]) -> list[int]:
    attached = [[] for _ in heights]
    answers = [-1] * len(queries)
    for index, (first, second) in enumerate(queries):
        first, second = min(first, second), max(first, second)
        if first == second or heights[first] < heights[second]:
            answers[index] = second
        else:
            attached[second].append((heights[first], index))
    heap = []
    for building, height in enumerate(heights):
        while heap and heap[0][0] < height:
            _, index = heappop(heap)
            answers[index] = building
        for request in attached[building]:
            heappush(heap, request)
    return answers


class Solution:
    def leftmostBuildingQueries(self, heights: list[int], queries: list[list[int]]) -> list[int]:
        return solve(heights, queries)
