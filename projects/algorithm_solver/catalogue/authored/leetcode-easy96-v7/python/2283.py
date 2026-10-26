"""2283. Check if Number Has Equal Digit Count and Digit Value (Easy).

Specification: https://leetcode.com/problems/check-if-number-has-equal-digit-count-and-digit-value/description/
"""


def solve(num: str) -> bool:
    """O(n) time, O(1) space for decimal digits; compare positions to digit frequencies."""
    counts = [0] * 10
    for character in num:
        counts[ord(character) - 48] += 1
    return all(counts[index] == ord(character) - 48 for index, character in enumerate(num))


class Solution:
    def digitCount(self, num: str) -> bool:
        return solve(num)
