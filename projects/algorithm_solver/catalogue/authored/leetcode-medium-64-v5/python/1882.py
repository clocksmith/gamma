"""1882. Process Tasks Using Servers: separate available-server priority from completion-time priority."""
from heapq import heapify, heappop, heappush


def solve(servers: list[int], tasks: list[int]) -> list[int]:
    """O((n + m) * log(n + 1)) time and O(n + m) space, with n servers and m tasks; inputs are read-only."""
    available = [(weight, index) for index, weight in enumerate(servers)]
    heapify(available)
    busy = []
    result = []
    time = 0
    for arrival, duration in enumerate(tasks):
        time = max(time, arrival)
        if not available and busy[0][0] > time:
            time = busy[0][0]
        while busy and busy[0][0] <= time:
            _, weight, index = heappop(busy)
            heappush(available, (weight, index))
        weight, index = heappop(available)
        result.append(index)
        heappush(busy, (time + duration, weight, index))
    return result


class Solution:
    def assignTasks(self, servers: list[int], tasks: list[int]) -> list[int]:
        return solve(servers, tasks)
