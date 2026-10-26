"""1118. Number of Days in a Month (Easy).

Specification: https://leetcode.com/problems/number-of-days-in-a-month/description/
"""


def solve(year: int, month: int) -> int:
    """O(1) time and space; Gregorian leap years include centuries only when divisible by 400."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    leap_year = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    return days[month - 1] + (1 if month == 2 and leap_year else 0)


class Solution:
    def numberOfDays(self, year: int, month: int) -> int:
        return solve(year, month)
