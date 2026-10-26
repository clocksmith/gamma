"""66. Plus One (Easy).

Specification: https://leetcode.com/problems/plus-one/description/
"""


def solve(digits: list[int]) -> list[int]:
    """O(n) time and space; propagate the carry through a fresh copy."""
    result = digits.copy()
    for index in range(len(result) - 1, -1, -1):
        if result[index] < 9:
            result[index] += 1
            return result
        result[index] = 0
    return [1] + result


class Solution:
    def plusOne(self, digits: list[int]) -> list[int]:
        return solve(digits)
