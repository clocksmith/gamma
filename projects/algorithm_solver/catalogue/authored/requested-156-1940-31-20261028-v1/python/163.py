"""Original frontend 163 variant; qualification unknown."""


def solve(nums, lower: int, upper: int):
    res = []
    prev = lower - 1
    for x in nums:
        if x - prev >= 2:
            res.append([prev + 1, x - 1])
        prev = x
    if (upper + 1) - prev >= 2:
        res.append([prev + 1, upper])
    return res


findMissingRanges = solve


class Solution:
    def findMissingRanges(self, nums, lower: int, upper: int):
        return solve(nums, lower, upper)
