"""2594. Minimum Time to Repair Cars: binary search time using exact integer repair capacities grouped by rank."""
from collections import Counter
from math import isqrt


def solve(ranks: list[int], cars: int) -> int:
    """O(n + u log T) time and O(u) auxiliary space, where T is the search bound and u is the number of ranks; inputs are read-only."""
    counts = Counter(ranks)
    low, high = 0, min(counts) * cars * cars
    while low < high:
        middle = (low + high) // 2
        repaired = 0
        for rank, count in counts.items():
            repaired += isqrt(middle // rank) * count
            if repaired >= cars:
                break
        if repaired >= cars:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def repairCars(self, ranks: list[int], cars: int) -> int:
        return solve(ranks, cars)
