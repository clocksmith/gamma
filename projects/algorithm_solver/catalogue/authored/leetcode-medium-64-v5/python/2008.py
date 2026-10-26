"""2008. Maximum Earnings From Taxi: schedule rides by finish point using binary search over prior earnings."""
from bisect import bisect_right


def solve(n: int, rides: list[list[int]]) -> int:
    """O(r * log(r + 1)) time and O(r) auxiliary space, with r rides; inputs are read-only."""
    ordered = sorted(rides, key=lambda ride: ride[1])
    ends = [0]
    earnings = [0]
    for start, end, tip in ordered:
        previous = bisect_right(ends, start) - 1
        candidate = earnings[previous] + end - start + tip
        ends.append(end)
        earnings.append(max(earnings[-1], candidate))
    return earnings[-1]


class Solution:
    def maxTaxiEarnings(self, n: int, rides: list[list[int]]) -> int:
        return solve(n, rides)
