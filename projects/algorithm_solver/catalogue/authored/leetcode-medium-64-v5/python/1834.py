"""1834. Single-Threaded CPU: schedule available tasks by processing time and original index."""
from heapq import heappop, heappush


def solve(tasks: list[list[int]]) -> list[int]:
    """O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted((start, duration, index) for index, (start, duration) in enumerate(tasks))
    heap = []
    result = []
    time = index = 0
    while index < len(ordered) or heap:
        if not heap:
            time = max(time, ordered[index][0])
        while index < len(ordered) and ordered[index][0] <= time:
            _, duration, original = ordered[index]
            heappush(heap, (duration, original))
            index += 1
        duration, original = heappop(heap)
        result.append(original)
        time += duration
    return result


class Solution:
    def getOrder(self, tasks: list[list[int]]) -> list[int]:
        return solve(tasks)
