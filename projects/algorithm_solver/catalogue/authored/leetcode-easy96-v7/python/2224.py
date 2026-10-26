"""2224. Minimum Number of Operations to Convert Time (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-operations-to-convert-time/description/
"""


def solve(current: str, correct: str) -> int:
    """O(1) time and space; correct is not earlier than current; greedily use 60, 15, 5, 1 minutes."""
    def minutes(time):
        return int(time[:2]) * 60 + int(time[3:])

    difference = minutes(correct) - minutes(current)
    operations = 0
    for step in (60, 15, 5, 1):
        operations += difference // step
        difference %= step
    return operations


class Solution:
    def convertTime(self, current: str, correct: str) -> int:
        return solve(current, correct)
