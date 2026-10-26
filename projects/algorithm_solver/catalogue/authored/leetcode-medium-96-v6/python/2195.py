"""2195. Append K Integers With Minimal Sum: fill missing positive-integer gaps using exact arithmetic-series sums."""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space on the stated integer domain; inputs are read-only."""
    remaining = k
    current = 1
    total = 0
    for value in sorted(set(nums)):
        if value < current:
            continue
        take = min(remaining, value - current)
        total += take * (2 * current + take - 1) // 2
        remaining -= take
        if remaining == 0:
            return total
        current = value + 1
    return total + remaining * (2 * current + remaining - 1) // 2


class Solution:
    def minimalKSum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
