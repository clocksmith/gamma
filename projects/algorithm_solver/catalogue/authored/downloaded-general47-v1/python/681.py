"""681. Next Closest Time (Medium).

Specification: https://leetcode.com/problems/next-closest-time/description/
"""


def solve(time: str) -> str:
    digits = {ch for ch in time if ch != ':'}
    start = int(time[:2]) * 60 + int(time[3:5])
    for delta in range(1, 1441):
        total = (start + delta) % 1440
        text = f"{total // 60:02d}:{total % 60:02d}"
        if all(ch in digits for ch in text if ch != ':'):
            return text
    return time


class Solution:
    def nextClosestTime(self, time: str) -> str:
        return solve(time)
