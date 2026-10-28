"""1010. Pairs of Songs With Total Durations Divisible by 60 (Medium).

Specification: https://leetcode.com/problems/pairs-of-songs-with-total-durations-divisible-by-60/description/
"""


def solve(time: list[int]) -> int:
    counts = [0] * 60
    for value in time:
        counts[value % 60] += 1
    total = 0
    total += counts[0] * (counts[0] - 1) // 2
    total += counts[30] * (counts[30] - 1) // 2
    for r in range(1, 30):
        total += counts[r] * counts[60 - r]
    return total


class Solution:
    def numPairsDivisibleBy60(self, time: list[int]) -> int:
        return solve(time)
