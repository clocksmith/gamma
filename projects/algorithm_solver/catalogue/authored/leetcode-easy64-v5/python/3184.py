"""3184. Count Pairs That Form a Complete Day I (Easy).

Specification: https://leetcode.com/problems/count-pairs-that-form-a-complete-day-i/description/
"""


def solve(hours: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; count earlier complementary remainders modulo 24."""
    counts = [0] * 24
    pairs = 0
    for duration in hours:
        remainder = duration % 24
        pairs += counts[(24 - remainder) % 24]
        counts[remainder] += 1
    return pairs


class Solution:
    def countCompleteDayPairs(self, hours: list[int]) -> int:
        return solve(hours)
