"""Original LeetCode 630 candidate; qualification unknown."""

import heapq

def solve(courses):
    chosen, elapsed = [], 0
    for duration, deadline in sorted(courses, key=lambda row: row[1]):
        elapsed += duration
        heapq.heappush(chosen, -duration)
        if elapsed > deadline:
            elapsed += heapq.heappop(chosen)
    return len(chosen)


class Solution:
    def scheduleCourse(self, courses):
        return solve(courses)
