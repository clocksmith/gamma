"""2279. Maximum Bags With Full Capacity of Rocks: fill bags in ascending order of their remaining capacity."""


def solve(capacity: list[int], rocks: list[int], additionalRocks: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    needed = sorted(limit - present for limit, present in zip(capacity, rocks))
    remaining = additionalRocks
    full = 0
    for amount in needed:
        if amount > remaining:
            break
        remaining -= amount
        full += 1
    return full


class Solution:
    def maximumBags(self, capacity: list[int], rocks: list[int], additionalRocks: int) -> int:
        return solve(capacity, rocks, additionalRocks)
