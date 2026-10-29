"""Hack2Hire 6a19022ac81f779dc6a231ab (Match Cyclic Shift to Descending Sequence) over an INFERRED spec; qualification unknown."""


def solve(nums):
    n = len(nums)
    ascent, count = -1, 0
    for i in range(n):
        if nums[i] < nums[(i + 1) % n]:
            count += 1
            ascent = i
            if count > 1:
                return -1
    if count == 0:
        return 0
    return (n - (ascent + 1)) % n


class Solution:
    def findDescendingShift(self, nums):
        return solve(nums)
