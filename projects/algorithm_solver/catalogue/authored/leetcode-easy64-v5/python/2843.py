"""2843. Count Symmetric Integers (Easy).

Specification: https://leetcode.com/problems/count-symmetric-integers/description/
"""


def solve(low: int, high: int) -> int:
    """O((high - low + 1) * d) time, O(d) space; d is maximum decimal digit count."""
    count = 0
    for value in range(low, high + 1):
        digits = str(value)
        if len(digits) % 2:
            continue
        half = len(digits) // 2
        difference = 0
        for index in range(half):
            difference += ord(digits[index]) - ord(digits[index + half])
        if difference == 0:
            count += 1
    return count


class Solution:
    def countSymmetricIntegers(self, low: int, high: int) -> int:
        return solve(low, high)
