"""252. Meeting Rooms (Easy).

Specification: https://leetcode.com/problems/meeting-rooms/description/
"""


def solve(intervals: list[list[int]]) -> bool:
    """O(n log n) time, O(n) space; compare adjacent sorted intervals without mutating input."""
    ordered = sorted(intervals, key=lambda interval: interval[0])
    for index in range(1, len(ordered)):
        if ordered[index][0] < ordered[index - 1][1]:
            return False
    return True


class Solution:
    def canAttendMeetings(self, intervals: list[list[int]]) -> bool:
        return solve(intervals)
