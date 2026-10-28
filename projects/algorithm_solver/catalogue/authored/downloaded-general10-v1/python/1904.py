"""1904. The Number of Full Rounds You Have Played (Easy).

Specification: https://leetcode.com/problems/the-number-of-full-rounds-you-have-played/description/
"""


def to_minutes(t: str) -> int:
    hours, minutes = t.split(":")
    return int(hours) * 60 + int(minutes)


def solve(loginTime: str, logoutTime: str) -> int:
    start = to_minutes(loginTime)
    end = to_minutes(logoutTime)
    if end <= start:
        end += 24 * 60
    return end // 15 - (start + 14) // 15


class Solution:
    def numberOfRounds(self, loginTime: str, logoutTime: str) -> int:
        return solve(loginTime, logoutTime)
