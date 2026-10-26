"""1672. Richest Customer Wealth (Easy).

Specification: https://leetcode.com/problems/richest-customer-wealth/description/
"""


def solve(accounts: list[list[int]]) -> int:
    """O(m * n) time, O(1) space; preserve accounts and its rows."""
    maximum = 0
    for balances in accounts:
        wealth = 0
        for balance in balances:
            wealth += balance
        maximum = max(maximum, wealth)
    return maximum


class Solution:
    def maximumWealth(self, accounts: list[list[int]]) -> int:
        return solve(accounts)
