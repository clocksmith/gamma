"""1482. Minimum Number of Days to Make m Bouquets: binary search the first feasible bloom day."""


def solve(bloomDay: list[int], m: int, k: int) -> int:
    """O(n log(D + 1)) time and O(1) auxiliary space for day range D; inputs are read-only."""
    if m > len(bloomDay) // k:
        return -1

    def can_make(day: int) -> bool:
        consecutive = bouquets = 0
        for bloom in bloomDay:
            if bloom > day:
                consecutive = 0
                continue
            consecutive += 1
            if consecutive == k:
                bouquets += 1
                if bouquets == m:
                    return True
                consecutive = 0
        return False

    low = min(bloomDay)
    high = max(bloomDay)
    while low < high:
        middle = (low + high) // 2
        if can_make(middle):
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minDays(self, bloomDay: list[int], m: int, k: int) -> int:
        return solve(bloomDay, m, k)
