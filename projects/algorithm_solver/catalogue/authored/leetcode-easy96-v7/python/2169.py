"""2169. Count Operations to Obtain Zero (Easy).

Specification: https://leetcode.com/problems/count-operations-to-obtain-zero/description/
"""


def solve(num1: int, num2: int) -> int:
    """O(log(max(num1, num2) + 1)) time, O(1) space; batch repeated subtractions by quotient."""
    first = num1
    second = num2
    operations = 0
    while first > 0 and second > 0:
        if first < second:
            first, second = second, first
        operations += first // second
        first %= second
    return operations


class Solution:
    def countOperations(self, num1: int, num2: int) -> int:
        return solve(num1, num2)
