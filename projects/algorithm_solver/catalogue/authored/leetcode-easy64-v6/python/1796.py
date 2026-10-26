"""1796. Second Largest Digit in a String (Easy).

Specification: https://leetcode.com/problems/second-largest-digit-in-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; track the two greatest distinct ASCII digits."""
    largest = -1
    second_largest = -1
    for character in s:
        if not '0' <= character <= '9':
            continue
        digit = ord(character) - ord('0')
        if digit > largest:
            second_largest = largest
            largest = digit
        elif second_largest < digit < largest:
            second_largest = digit
    return second_largest


class Solution:
    def secondHighest(self, s: str) -> int:
        return solve(s)
