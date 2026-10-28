"""3315. Construct the Minimum Bitwise Array II (Medium).

Specification: https://leetcode.com/problems/construct-the-minimum-bitwise-array-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    out = []
    for num in nums:
        if num == 2:
            out.append(-1)
        else:
            low = (num + 1) & (-(num + 1))
            out.append(num - low // 2)
    return out


class Solution:
    def minBitwiseArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
