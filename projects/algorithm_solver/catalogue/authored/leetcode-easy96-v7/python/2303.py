"""2303. Calculate Amount Paid in Taxes (Easy).

Specification: https://leetcode.com/problems/calculate-amount-paid-in-taxes/description/
"""


def solve(brackets: list[list[int]], income: int) -> float:
    """O(n) time, O(1) space; accumulate integer percentage-units then divide once; preserve brackets."""
    previous = 0
    percentage_units = 0
    for upper, percent in brackets:
        taxable = min(income, upper) - previous
        if taxable > 0:
            percentage_units += taxable * percent
        if income <= upper:
            break
        previous = upper
    return percentage_units / 100


class Solution:
    def calculateTax(self, brackets: list[list[int]], income: int) -> float:
        return solve(brackets, income)
