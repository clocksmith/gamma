def lower_bound(values: list[int], target: int) -> int:
    left = 0
    right = len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def searchInsert(self, nums: list[int], target: int) -> int:
        return lower_bound(nums, target)
