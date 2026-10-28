"""1942. The Number of the Smallest Unoccupied Chair (Medium).

Specification: https://leetcode.com/problems/the-number-of-the-smallest-unoccupied-chair/description/
"""


def solve(times: list[list[int]], targetFriend: int) -> int:
    order = sorted(range(len(times)), key=lambda i: times[i][0])
    occupied = []
    free = []
    next_chair = 0
    for i in order:
        arrival, departure = times[i]
        still = []
        for dep, chair in occupied:
            if dep <= arrival:
                free.append(chair)
            else:
                still.append((dep, chair))
        occupied = still
        free.sort()
        if free:
            chair = free.pop(0)
        else:
            chair = next_chair
            next_chair += 1
        if i == targetFriend:
            return chair
        occupied.append((departure, chair))
    return -1


class Solution:
    def smallestChair(self, times: list[list[int]], targetFriend: int) -> int:
        return solve(times, targetFriend)
