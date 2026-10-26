"""1176. Diet Plan Performance (Easy).

Specification: https://leetcode.com/problems/diet-plan-performance/description/
"""


def solve(calories: list[int], k: int, lower: int, upper: int) -> int:
    """O(n) time, O(1) space; score every overlapping k-day window with strict bounds."""
    total = 0
    for index in range(k):
        total += calories[index]
    score = -1 if total < lower else 1 if total > upper else 0
    for index in range(k, len(calories)):
        total += calories[index] - calories[index - k]
        if total < lower:
            score -= 1
        elif total > upper:
            score += 1
    return score


class Solution:
    def dietPlanPerformance(self, calories: list[int], k: int, lower: int, upper: int) -> int:
        return solve(calories, k, lower, upper)
