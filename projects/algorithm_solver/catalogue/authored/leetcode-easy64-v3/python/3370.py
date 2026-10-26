"""3370. Smallest Number With All Set Bits (Easy).

Specification: https://leetcode.com/problems/smallest-number-with-all-set-bits/description/
"""


def solve(n: int) -> int:
    """O(log n) time, O(1) space; grow numbers of the form 2^bits - 1."""
    result = 1
    while result < n:
        result = result * 2 + 1
    return result


class Solution:
    def smallestNumber(self, n: int) -> int:
        return solve(n)
