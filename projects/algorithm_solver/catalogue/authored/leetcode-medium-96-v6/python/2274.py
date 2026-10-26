"""2274. Maximum Consecutive Floors Without Special Floors: measure gaps between sorted special floors and the two building boundaries."""


def solve(bottom: int, top: int, special: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    previous = bottom - 1
    best = 0
    for floor in sorted(special):
        best = max(best, floor - previous - 1)
        previous = floor
    return max(best, top - previous)


class Solution:
    def maxConsecutive(self, bottom: int, top: int, special: list[int]) -> int:
        return solve(bottom, top, special)
