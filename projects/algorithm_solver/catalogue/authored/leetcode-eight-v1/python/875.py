"""Binary search the first feasible integer eating speed."""


def solve(piles: list[int], h: int) -> int:
    """O(n log(max(piles))) time, O(1) auxiliary space; do not mutate piles."""
    low, high = 1, max(piles)
    while low < high:
        speed = (low + high) // 2
        hours = 0
        for pile in piles:
            hours += (pile + speed - 1) // speed
            if hours > h:
                break
        if hours <= h:
            high = speed
        else:
            low = speed + 1
    return low


class Solution:
    def minEatingSpeed(self, piles: list[int], h: int) -> int:
        return solve(piles, h)
