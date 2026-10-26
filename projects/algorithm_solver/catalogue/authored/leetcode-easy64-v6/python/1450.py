"""1450. Number of Students Doing Homework at a Given Time (Easy).

Specification: https://leetcode.com/problems/number-of-students-doing-homework-at-a-given-time/description/
"""


def solve(startTime: list[int], endTime: list[int], queryTime: int) -> int:
    """O(n) time, O(1) space; interval endpoints are inclusive; preserve inputs."""
    result = 0
    for index in range(len(startTime)):
        if startTime[index] <= queryTime <= endTime[index]:
            result += 1
    return result


class Solution:
    def busyStudent(self, startTime: list[int], endTime: list[int], queryTime: int) -> int:
        return solve(startTime, endTime, queryTime)
