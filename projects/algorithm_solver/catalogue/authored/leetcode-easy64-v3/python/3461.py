"""3461. Check If Digits Are Equal in String After Operations I (Easy).

Specification: https://leetcode.com/problems/check-if-digits-are-equal-in-string-after-operations-i/description/
"""


def solve(s: str) -> bool:
    """O(n^2) time, O(n) space; update a local digit buffer from left to right."""
    digits = [ord(character) - ord('0') for character in s]
    length = len(digits)
    while length > 2:
        for index in range(length - 1):
            digits[index] = (digits[index] + digits[index + 1]) % 10
        length -= 1
    return digits[0] == digits[1]


class Solution:
    def hasSameDigits(self, s: str) -> bool:
        return solve(s)
