"""1507. Reformat Date (Easy).

Specification: https://leetcode.com/problems/reformat-date/description/
"""


MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}


def _pad(value):
    return f"0{value}" if value < 10 else str(value)


def solve(date: str) -> str:
    parts = date.split(' ')
    day = int(''.join(ch for ch in parts[0] if ch.isdigit()))
    month = MONTHS[parts[1]]
    year = parts[2]
    return f"{year}-{_pad(month)}-{_pad(day)}"


class Solution:
    def reformatDate(self, date: str) -> str:
        return solve(date)
