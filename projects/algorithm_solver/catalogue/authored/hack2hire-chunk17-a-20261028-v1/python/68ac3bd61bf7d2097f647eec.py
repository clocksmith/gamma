"""Hack2Hire 68ac3bd61bf7d2097f647eec (Subarray with Most Target Element) over an INFERRED spec; qualification unknown."""


def solve(nums, targetIndex, windowSize):
    target = nums[targetIndex]
    count = 0
    for i in range(windowSize):
        if nums[i] == target:
            count += 1
    best = count
    start = 0
    for i in range(1, len(nums) - windowSize + 1):
        if nums[i - 1] == target:
            count -= 1
        if nums[i + windowSize - 1] == target:
            count += 1
        if count > best:
            best = count
            start = i
    return start


class Solution:
    def mostTargetWindow(self, nums, targetIndex, windowSize):
        return solve(nums, targetIndex, windowSize)
