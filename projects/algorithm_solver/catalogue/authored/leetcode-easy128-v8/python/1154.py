"""1154. Day of the Year (Easy).

Specification: https://leetcode.com/problems/day-of-the-year/description/
"""


def solve(date: str) -> int:
    """O(1) time and space for fixed-format dates; sum earlier Gregorian month lengths."""
    year, month, day = int(date[:4]), int(date[5:7]), int(date[8:10])
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
        days[1] = 29
    result = day
    for index in range(month - 1):
        result += days[index]
    return result


class Solution:
    def dayOfYear(self, date: str) -> int:
        return solve(date)
