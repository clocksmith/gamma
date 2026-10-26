"""2980. Check if Bitwise OR Has Trailing Zeros (Easy).

Specification: https://leetcode.com/problems/check-if-bitwise-or-has-trailing-zeros/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) time, O(1) space; at least two even operands are necessary and sufficient."""
    evens = 0
    for value in nums:
        if value % 2 == 0:
            evens += 1
        if evens >= 2:
            return True
    return False


class Solution:
    def hasTrailingZeros(self, nums: list[int]) -> bool:
        return solve(nums)
