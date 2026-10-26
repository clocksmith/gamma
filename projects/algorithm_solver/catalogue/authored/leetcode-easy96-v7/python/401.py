"""401. Binary Watch (Easy).

Specification: https://leetcode.com/problems/binary-watch/description/
"""


def solve(turnedOn: int) -> list[str]:
    """O(1) bounded enumeration of 720 times; return fresh strings in chronological order."""
    def bit_count(value):
        count = 0
        while value > 0:
            value &= value - 1
            count += 1
        return count

    result = []
    for hour in range(12):
        for minute in range(60):
            if bit_count(hour) + bit_count(minute) == turnedOn:
                result.append(str(hour) + ':' + str(minute).zfill(2))
    return result


class Solution:
    def readBinaryWatch(self, turnedOn: int) -> list[str]:
        return solve(turnedOn)
