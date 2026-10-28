"""1011. Capacity To Ship Packages Within D Days (Medium).

Specification: https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/description/
"""


def _days_needed(weights, capacity):
    days = 1
    load = 0
    for value in weights:
        if load + value > capacity:
            days += 1
            load = value
        else:
            load += value
    return days


def solve(weights: list[int], days: int) -> int:
    left = max(weights)
    right = sum(weights)
    while left < right:
        mid = (left + right) // 2
        if _days_needed(weights, mid) <= days:
            right = mid
        else:
            left = mid + 1
    return left


class Solution:
    def shipWithinDays(self, weights: list[int], days: int) -> int:
        return solve(weights, days)
