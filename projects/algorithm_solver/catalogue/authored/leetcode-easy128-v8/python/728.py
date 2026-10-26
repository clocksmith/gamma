"""728. Self Dividing Numbers (Easy).

Specification: https://leetcode.com/problems/self-dividing-numbers/description/
"""


def solve(left: int, right: int) -> list[int]:
    """O((right - left + 1) * d) time, O(1) auxiliary space excluding output; reject zero digits."""
    result = []
    for value in range(left, right + 1):
        remaining = value
        valid = True
        while remaining > 0:
            digit = remaining % 10
            if digit == 0 or value % digit != 0:
                valid = False
                break
            remaining //= 10
        if valid:
            result.append(value)
    return result


class Solution:
    def selfDividingNumbers(self, left: int, right: int) -> list[int]:
        return solve(left, right)
