"""3314. Construct the Minimum Bitwise Array I (Easy).

Specification: https://leetcode.com/problems/construct-the-minimum-bitwise-array-i/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n log M) time, O(n) result space; M <= 1000; clear the highest trailing one."""
    result = []
    for value in nums:
        if value % 2 == 0:
            result.append(-1)
            continue
        bit = 1
        while value & bit:
            bit *= 2
        result.append(value - bit // 2)
    return result


class Solution:
    def minBitwiseArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
