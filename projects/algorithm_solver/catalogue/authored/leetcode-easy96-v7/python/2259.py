"""2259. Remove Digit From Number to Maximize Result (Easy).

Specification: https://leetcode.com/problems/remove-digit-from-number-to-maximize-result/description/
"""


def solve(number: str, digit: str) -> str:
    """O(n) time and output space; remove before the first increase, otherwise remove the last occurrence."""
    last = -1
    for index, character in enumerate(number):
        if character != digit:
            continue
        last = index
        if index + 1 < len(number) and number[index + 1] > digit:
            return number[:index] + number[index + 1:]
    return number[:last] + number[last + 1:]


class Solution:
    def removeDigit(self, number: str, digit: str) -> str:
        return solve(number, digit)
