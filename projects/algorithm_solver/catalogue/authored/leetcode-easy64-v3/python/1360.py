"""1360. Number of Days Between Two Dates (Easy).

Specification: https://leetcode.com/problems/number-of-days-between-two-dates/description/
"""


def solve(date1: str, date2: str) -> int:
    """O(1) time and space for fixed-format Gregorian dates; no timezone conversion."""
    def ordinal(date: str) -> int:
        year, month, day = map(int, date.split('-'))
        previous_year = year - 1
        days = (365 * previous_year + previous_year // 4
                - previous_year // 100 + previous_year // 400 + day)
        month_lengths = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        for index in range(month - 1):
            days += month_lengths[index]
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        if month > 2 and leap:
            days += 1
        return days

    return abs(ordinal(date1) - ordinal(date2))


class Solution:
    def daysBetweenDates(self, date1: str, date2: str) -> int:
        return solve(date1, date2)
