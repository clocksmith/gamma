"""1323. Maximum 69 Number (Easy).

Specification: https://leetcode.com/problems/maximum-69-number/description/
"""


def solve(num: int) -> int:
    """O(d) time and space; d is the number of decimal digits."""
    return int(str(num).replace('6', '9', 1))


class Solution:
    def maximum69Number(self, num: int) -> int:
        return solve(num)
