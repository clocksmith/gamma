"""2566. Maximum Difference by Remapping a Digit (Easy).

Specification: https://leetcode.com/problems/maximum-difference-by-remapping-a-digit/description/
"""


def solve(num: int) -> int:
    """O(d) time and space; remap all occurrences, allowing leading zeroes."""
    digits = str(num)
    high_target = '9'
    for character in digits:
        if character != '9':
            high_target = character
            break
    low_target = digits[0]
    maximum = 0
    minimum = 0
    for character in digits:
        digit = ord(character) - ord('0')
        maximum = maximum * 10 + (9 if character == high_target else digit)
        minimum = minimum * 10 + (0 if character == low_target else digit)
    return maximum - minimum


class Solution:
    def minMaxDifference(self, num: int) -> int:
        return solve(num)
