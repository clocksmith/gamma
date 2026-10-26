"""3723. Maximize Sum of Squares of Digits."""
from __future__ import annotations


def solve(num: int, sum: int) -> str:
    """O(num) time and output space; concentrating the digit sum maximizes the convex square objective."""
    if sum > 9 * num:
        return ''
    answer = []
    remaining = sum
    for _ in range(num):
        digit = min(9, remaining)
        answer.append(str(digit))
        remaining -= digit
    return ''.join(answer)


class Solution:
    def maxSumOfSquares(self, num: int, sum: int) -> str:
        return solve(num, sum)
