"""1491. Average Salary Excluding the Minimum and Maximum Salary (Easy).

Specification: https://leetcode.com/problems/average-salary-excluding-the-minimum-and-maximum-salary/description/
"""


def solve(salary: list[int]) -> float:
    """O(n) time, O(1) space; preserve salary; the final division is floating point."""
    total = 0
    lowest = salary[0]
    highest = salary[0]
    for value in salary:
        total += value
        lowest = min(lowest, value)
        highest = max(highest, value)
    return (total - lowest - highest) / (len(salary) - 2)


class Solution:
    def average(self, salary: list[int]) -> float:
        return solve(salary)
