"""2437. Number of Valid Clock Times (Easy).

Specification: https://leetcode.com/problems/number-of-valid-clock-times/description/
"""


def solve(time: str) -> int:
    """O(1) time and space; independently count matching hours and minutes in the fixed clock domain."""
    hours = 0
    minutes = 0
    for hour in range(24):
        text = str(hour).zfill(2)
        if (time[0] == '?' or time[0] == text[0]) and (time[1] == '?' or time[1] == text[1]):
            hours += 1
    for minute in range(60):
        text = str(minute).zfill(2)
        if (time[3] == '?' or time[3] == text[0]) and (time[4] == '?' or time[4] == text[1]):
            minutes += 1
    return hours * minutes


class Solution:
    def countTime(self, time: str) -> int:
        return solve(time)
