"""3483. Unique 3-Digit Even Numbers (Easy).

Specification: https://leetcode.com/problems/unique-3-digit-even-numbers/description/
"""


def solve(digits: list[int]) -> int:
    """O(n + 450) time, O(1) space; enumerate digit values with multiplicities, not indices."""
    counts = [0] * 10
    for digit in digits:
        counts[digit] += 1
    result = 0
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
                    result += 1
            counts[tens] += 1
        counts[hundreds] += 1
    return result


class Solution:
    def totalNumbers(self, digits: list[int]) -> int:
        return solve(digits)
