"""475. Heaters."""

from bisect import bisect_left, bisect_right

def solve(houses: list[int], heaters: list[int]) -> int:
    ordered = sorted(heaters)
    answer = 0
    for house in houses:
        index = bisect_left(ordered, house)
        left = house - ordered[index - 1] if index else float('inf')
        right = ordered[index] - house if index < len(ordered) else float('inf')
        answer = max(answer, min(left, right))
    return answer


class Solution:
    def findRadius(self, houses: list[int], heaters: list[int]) -> int:
        return solve(houses, heaters)
