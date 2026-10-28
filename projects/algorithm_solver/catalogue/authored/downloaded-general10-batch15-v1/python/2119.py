"""2119. A Number After a Double Reversal (Easy).

Specification: https://leetcode.com/problems/a-number-after-a-double-reversal/description/
"""


def reverse_number(num: int) -> int:
    return int(str(num)[::-1])


def solve(num: int) -> bool:
    return reverse_number(reverse_number(num)) == num


class Solution:
    def isSameAfterReversals(self, num: int) -> bool:
        return solve(num)
