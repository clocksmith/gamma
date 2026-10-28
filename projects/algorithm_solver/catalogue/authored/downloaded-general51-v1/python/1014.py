"""1014. Best Sightseeing Pair (Medium).

Specification: https://leetcode.com/problems/best-sightseeing-pair/description/
"""


def solve(values: list[int]) -> int:
    best = 0
    best_left = values[0] + 0
    for j in range(1, len(values)):
        best = max(best, best_left + values[j] - j)
        best_left = max(best_left, values[j] + j)
    return best


class Solution:
    def maxScoreSightseeingPair(self, values: list[int]) -> int:
        return solve(values)
