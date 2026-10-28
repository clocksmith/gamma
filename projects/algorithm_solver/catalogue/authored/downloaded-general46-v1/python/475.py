"""475. Heaters (Medium).

Specification: https://leetcode.com/problems/heaters/description/
"""


def solve(houses: list[int], heaters: list[int]) -> int:
    ordered = sorted(heaters)
    radius = 0
    for house in houses:
        left, right = 0, len(ordered) - 1
        best = float('inf')
        while left <= right:
            mid = (left + right) // 2
            best = min(best, abs(ordered[mid] - house))
            if ordered[mid] < house:
                left = mid + 1
            else:
                right = mid - 1
        radius = max(radius, best)
    return radius


class Solution:
    def findRadius(self, houses: list[int], heaters: list[int]) -> int:
        return solve(houses, heaters)
