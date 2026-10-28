"""2295. Replace Elements in an Array (Medium).

Specification: https://leetcode.com/problems/replace-elements-in-an-array/description/
"""


def solve(nums: list[int], operations: list[list[int]]) -> list[int]:
    pos = {v: i for i, v in enumerate(nums)}
    out = nums[:]
    for old, new in operations:
        idx = pos.pop(old)
        out[idx] = new
        pos[new] = idx
    return out


class Solution:
    def arrayChange(self, nums, operations) -> object:
        return solve(nums, operations)
