"""1629. Slowest Key (Easy).

Specification: https://leetcode.com/problems/slowest-key/description/
"""


def solve(releaseTimes: list[int], keysPressed: str) -> str:
    """O(n) time, O(1) space; break equal-duration ties by the greatest key; preserve inputs."""
    previous_release = 0
    longest_duration = -1
    slowest = ''
    for index, released_at in enumerate(releaseTimes):
        duration = released_at - previous_release
        key = keysPressed[index]
        if duration > longest_duration or (duration == longest_duration and key > slowest):
            longest_duration = duration
            slowest = key
        previous_release = released_at
    return slowest


class Solution:
    def slowestKey(self, releaseTimes: list[int], keysPressed: str) -> str:
        return solve(releaseTimes, keysPressed)
