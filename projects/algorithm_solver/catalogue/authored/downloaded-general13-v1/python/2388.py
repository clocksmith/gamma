"""2388. Replace Elements in an Array (Medium).

Specification: https://leetcode.com/problems/replace-elements-in-an-array/description/
"""


def solve(nums, operations):
    pos = {v: i for i, v in enumerate(nums)}
    for a, b in operations:
        idx = pos.pop(a)
        nums[idx] = b
        pos[b] = idx
    return nums


class Solution:
    def arrayChange(self, nums, operations):
        return solve(nums, operations)
