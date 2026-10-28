"""1185. Day of the Week (Easy).

Specification: https://leetcode.com/problems/day-of-the-week/description/
"""


DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def solve(day: int, month: int, year: int) -> str:
    days = 0
    for y in range(1971, year):
        days += 366 if _is_leap(y) else 365
    for m in range(1, month):
        days += MONTH_DAYS[m - 1] + (1 if m == 2 and _is_leap(year) else 0)
    days += day - 1
    return DAYS[(days + 5) % 7]


class Solution:
    def dayOfTheWeek(self, day: int, month: int, year: int) -> str:
        return solve(day, month, year)
