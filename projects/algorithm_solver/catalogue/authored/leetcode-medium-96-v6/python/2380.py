"""2380. Time Needed to Rearrange a Binary String: track how zeros ahead and earlier moving ones delay each subsequent one."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    zeros = seconds = 0
    for character in s:
        if character == '0':
            zeros += 1
        elif zeros:
            seconds = max(seconds + 1, zeros)
    return seconds


class Solution:
    def secondsToRemoveOccurrences(self, s: str) -> int:
        return solve(s)
