"""3945. Digit Frequency Score (Easy).

Specification: https://leetcode.com/problems/digit-frequency-score/description/
"""


def solve(n: int) -> int:
    """O(d) time, O(1) space; summing each digit once equals the frequency-weighted score."""
    remaining = n
    score = 0
    while remaining > 0:
        score += remaining % 10
        remaining //= 10
    return score


class Solution:
    def digitFrequencyScore(self, n: int) -> int:
        return solve(n)
