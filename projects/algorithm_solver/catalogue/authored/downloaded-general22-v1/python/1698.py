"""1698. Maximum Number of Events That Can Be Attended (Medium).

Specification: https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended/description/
"""


import heapq


def solve(events: list[list[int]]) -> int:
    events = sorted(events)
    heap = []
    day = 0
    i = 0
    count = 0
    while i < len(events) or heap:
        if not heap:
            day = max(day, events[i][0])
        while i < len(events) and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            count += 1
            day += 1
    return count


class Solution:
    def maxEvents(self, events: list[list[int]]) -> int:
        return solve(events)
