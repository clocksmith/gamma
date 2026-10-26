"""2532. Time to Cross a Bridge. Event simulation with separate waiting and working heaps on both banks."""

from heapq import heapify, heappop, heappush


def solve(n: int, k: int, time: list[list[int]]) -> int:
    """O((n+k) log(k+1)) time and O(k) space. Inputs are preserved."""
    priority = [(-(row[0] + row[2]), -index) for index, row in enumerate(time)]
    waiting_left = priority.copy()
    heapify(waiting_left)
    waiting_right = []
    working_left = []
    working_right = []
    remaining = n
    clock = 0
    while remaining or waiting_right or working_right:
        while working_left and working_left[0][0] <= clock:
            _, worker = heappop(working_left)
            heappush(waiting_left, priority[worker])
        while working_right and working_right[0][0] <= clock:
            _, worker = heappop(working_right)
            heappush(waiting_right, priority[worker])
        if waiting_right:
            _, negative_worker = heappop(waiting_right)
            worker = -negative_worker
            clock += time[worker][2]
            heappush(working_left, (clock + time[worker][3], worker))
        elif remaining and waiting_left:
            _, negative_worker = heappop(waiting_left)
            worker = -negative_worker
            clock += time[worker][0]
            remaining -= 1
            heappush(working_right, (clock + time[worker][1], worker))
        else:
            next_left = working_left[0][0] if remaining and working_left else float("inf")
            next_right = working_right[0][0] if working_right else float("inf")
            clock = min(next_left, next_right)
    return clock


class Solution:
    def findCrossingTime(self, n: int, k: int, time: list[list[int]]) -> int:
        return solve(n, k, time)
