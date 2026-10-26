"""1056. Confusing Number (Easy).

Specification: https://leetcode.com/problems/confusing-number/description/
"""


def solve(n: int) -> bool:
    """O(d) time, O(1) space; rotate valid digits in reverse order and require a changed value."""
    rotated_digit = [0, 1, -1, -1, -1, -1, 9, -1, 8, 6]
    remaining = n
    rotated = 0
    while remaining > 0:
        digit = remaining % 10
        if rotated_digit[digit] < 0:
            return False
        rotated = rotated * 10 + rotated_digit[digit]
        remaining //= 10
    return rotated != n


class Solution:
    def confusingNumber(self, n: int) -> bool:
        return solve(n)
