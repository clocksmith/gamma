"""3379. Transformed Array (Easy).

Specification: https://leetcode.com/problems/transformed-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    n = len(nums)
    res = []
    for i, x in enumerate(nums):
        if x == 0:
            res.append(0)
        else:
            res.append(nums[(i + x) % n])
    return res


class Solution:
    def constructTransformedArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
