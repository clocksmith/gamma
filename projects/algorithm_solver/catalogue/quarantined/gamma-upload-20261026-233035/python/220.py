"""220. Contains Duplicate III."""
def solve(nums: list[int], indexDiff: int, valueDiff: int) -> bool:
    if valueDiff < 0:
        return False
    width = valueDiff + 1
    buckets = {}
    for index, value in enumerate(nums):
        bucket = value // width
        if bucket in buckets:
            return True
        if bucket - 1 in buckets and value - buckets[bucket - 1] <= valueDiff:
            return True
        if bucket + 1 in buckets and buckets[bucket + 1] - value <= valueDiff:
            return True
        buckets[bucket] = value
        if index >= indexDiff:
            del buckets[nums[index - indexDiff] // width]
    return False

class Solution:
    def containsNearbyAlmostDuplicate(self, nums, indexDiff, valueDiff):
        return solve(nums, indexDiff, valueDiff)
