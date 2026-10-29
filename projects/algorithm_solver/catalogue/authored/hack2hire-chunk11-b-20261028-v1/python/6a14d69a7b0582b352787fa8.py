"""Hack2Hire 6a14d69a7b0582b352787fa8 (Jumping by Height) over an INFERRED spec; qualification unknown."""


def solve(nums, index):
    n = len(nums)
    seen = set()  # states 2 * position + (1 when the next jump goes left)
    position, height, left, jumps = index, nums[index], True, 0
    while True:
        state = 2 * position + (1 if left else 0)
        if state in seen:
            return -1
        seen.add(state)
        target = position - height if left else position + height
        if target < 0 or target >= n:
            return jumps
        position, height, left, jumps = target, nums[target], not left, jumps + 1


class Solution:
    def countJumps(self, nums, index):
        return solve(nums, index)
