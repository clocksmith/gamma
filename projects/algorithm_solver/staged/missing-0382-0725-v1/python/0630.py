"""630. Course Schedule III."""

from heapq import heappush, heappop

def solve(courses: list[list[int]]) -> int:
    heap = []
    elapsed = 0
    for duration, deadline in sorted(courses, key=lambda course: course[1]):
        elapsed += duration
        heappush(heap, -duration)
        if elapsed > deadline:
            elapsed += heappop(heap)
    return len(heap)


class Solution:
    def scheduleCourse(self, courses: list[list[int]]) -> int:
        return solve(courses)
