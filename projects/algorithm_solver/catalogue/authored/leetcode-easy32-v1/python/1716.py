"""1716. Calculate Money in Leetcode Bank (Easy).

Specification: https://leetcode.com/problems/calculate-money-in-leetcode-bank/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; sum complete weeks and the final partial week."""
    weeks, days = divmod(n, 7)
    complete_weeks = 28 * weeks + 7 * weeks * (weeks - 1) // 2
    remaining_days = days * (weeks + 1) + days * (days - 1) // 2
    return complete_weeks + remaining_days


class Solution:
    def totalMoney(self, n: int) -> int:
        return solve(n)
