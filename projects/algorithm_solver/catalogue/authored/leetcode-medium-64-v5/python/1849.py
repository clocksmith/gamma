"""1849. Splitting a String Into Descending Consecutive Values: try each first value and consume the uniquely determined positive successors."""


def solve(s: str) -> bool:
    """O(n^2) digit steps and O(n) bits of integer storage on the at-most-20-digit domain; inputs are read-only."""
    def matches(start: int, previous: int) -> bool:
        while start < len(s):
            if previous == 0:
                return False
            expected = previous - 1
            if expected == 0:
                return all(s[index] == '0' for index in range(start, len(s)))
            value = 0
            while start < len(s) and value < expected:
                value = value * 10 + ord(s[start]) - ord('0')
                start += 1
            if value != expected:
                return False
            previous = expected
        return True

    first = 0
    for end in range(len(s) - 1):
        first = first * 10 + ord(s[end]) - ord('0')
        if matches(end + 1, first):
            return True
    return False


class Solution:
    def splitString(self, s: str) -> bool:
        return solve(s)
