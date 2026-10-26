"""3688. Bitwise OR of Even Numbers in an Array (Easy).

Specification: https://leetcode.com/problems/bitwise-or-of-even-numbers-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; values in [1, 100] make bitwise arithmetic safe."""
    result = 0
    for value in nums:
        if value % 2 == 0:
            result |= value
    return result


class Solution:
    def evenNumberBitwiseORs(self, nums: list[int]) -> int:
        return solve(nums)
