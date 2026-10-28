"""189. Rotate Array (Medium).

Specification: https://leetcode.com/problems/rotate-array/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    if n == 0:
        return []
    steps = k % n
    return nums[n - steps:] + nums[:n - steps]


class Solution:
    def rotate(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
