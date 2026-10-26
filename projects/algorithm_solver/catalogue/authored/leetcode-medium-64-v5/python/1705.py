"""1705. Maximum Number of Eaten Apples: eat the earliest-expiring apple and batch the remaining days after arrivals stop."""
from heapq import heappop, heappush


def solve(apples: list[int], days: list[int]) -> int:
    """O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    heap = []
    eaten = 0
    for day, count in enumerate(apples):
        if count > 0 and days[day] > 0:
            heappush(heap, (day + days[day], count))
        while heap and heap[0][0] <= day:
            heappop(heap)
        if heap:
            expiry, count = heappop(heap)
            eaten += 1
            if count > 1:
                heappush(heap, (expiry, count - 1))
    day = len(apples)
    while heap:
        expiry, count = heappop(heap)
        if expiry <= day:
            continue
        taken = min(count, expiry - day)
        eaten += taken
        day += taken
    return eaten


class Solution:
    def eatenApples(self, apples: list[int], days: list[int]) -> int:
        return solve(apples, days)
