"""1742. Maximum Number of Balls in a Box (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-balls-in-a-box/description/
"""


def solve(lowLimit: int, highLimit: int) -> int:
    """O((highLimit - lowLimit + 1) * d) time, O(d) space; d is the digit bound."""
    counts = {}
    result = 0
    for value in range(lowLimit, highLimit + 1):
        remaining = value
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        count = counts.get(digit_sum, 0) + 1
        counts[digit_sum] = count
        result = max(result, count)
    return result


class Solution:
    def countBalls(self, lowLimit: int, highLimit: int) -> int:
        return solve(lowLimit, highLimit)
