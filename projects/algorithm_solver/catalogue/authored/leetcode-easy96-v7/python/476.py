"""476. Number Complement (Easy).

Specification: https://leetcode.com/problems/number-complement/description/
"""


def solve(num: int) -> int:
    """O(log num) time, O(1) space; complement only significant bits of a positive integer."""
    boundary = 1
    while boundary <= num:
        boundary *= 2
    return boundary - 1 - num


class Solution:
    def findComplement(self, num: int) -> int:
        return solve(num)
