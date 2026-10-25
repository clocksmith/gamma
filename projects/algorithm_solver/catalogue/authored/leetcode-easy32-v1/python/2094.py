"""2094. Finding 3-Digit Even Numbers (Easy).

Specification: https://leetcode.com/problems/finding-3-digit-even-numbers/description/
"""


def solve(digits: list[int]) -> list[int]:
    """O(n + 450) time, O(1) auxiliary space excluding sorted output."""
    counts = [0] * 10
    for digit in digits:
        counts[digit] += 1
    result = []
    for hundreds in range(1, 10):
        if counts[hundreds] == 0:
            continue
        counts[hundreds] -= 1
        for tens in range(10):
            if counts[tens] == 0:
                continue
            counts[tens] -= 1
            for units in range(0, 10, 2):
                if counts[units] > 0:
                    result.append(100 * hundreds + 10 * tens + units)
            counts[tens] += 1
        counts[hundreds] += 1
    return result


class Solution:
    def findEvenNumbers(self, digits: list[int]) -> list[int]:
        return solve(digits)
