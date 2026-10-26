"""2409. Count Days Spent Together (Easy).

Specification: https://leetcode.com/problems/count-days-spent-together/description/
"""


def solve(arriveAlice: str, leaveAlice: str, arriveBob: str, leaveBob: str) -> int:
    """O(1) time and space for a non-leap year; compute the inclusive intersection of day-of-year intervals."""
    month_lengths = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    def day_of_year(date):
        month = int(date[:2])
        day = int(date[3:])
        for index in range(month - 1):
            day += month_lengths[index]
        return day

    start = max(day_of_year(arriveAlice), day_of_year(arriveBob))
    end = min(day_of_year(leaveAlice), day_of_year(leaveBob))
    return max(0, end - start + 1)


class Solution:
    def countDaysTogether(self, arriveAlice: str, leaveAlice: str, arriveBob: str, leaveBob: str) -> int:
        return solve(arriveAlice, leaveAlice, arriveBob, leaveBob)
