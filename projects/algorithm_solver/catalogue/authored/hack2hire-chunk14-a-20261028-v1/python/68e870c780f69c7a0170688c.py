"""Hack2Hire 68e870c780f69c7a0170688c (Subset Sum Target) over an INFERRED spec; qualification unknown."""


def solve(nums, target):
    mask = (1 << (target + 1)) - 1
    reach = 1
    for value in nums:
        reach = (reach | (reach << value)) & mask
        if reach >> target & 1:
            return True
    return bool(reach >> target & 1)


class Solution:
    def canReachTarget(self, nums, target):
        return solve(nums, target)
