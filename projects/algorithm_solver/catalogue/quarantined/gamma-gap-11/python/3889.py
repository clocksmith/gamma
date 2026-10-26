"""3889. Mirror Frequency Distance."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) time and O(1) alphabet space; count each alphabetic or numeric mirror pair exactly once."""
    letters = [0] * 26
    digits = [0] * 10
    for char in s:
        if '0' <= char <= '9':
            digits[ord(char) - 48] += 1
        else:
            letters[ord(char) - 97] += 1
    return sum(abs(letters[index] - letters[25 - index]) for index in range(13)) + sum(abs(digits[index] - digits[9 - index]) for index in range(5))


class Solution:
    def mirrorDistance(self, s: str) -> int:
        return solve(s)
