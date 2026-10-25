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
    def search(self, nums: list[int], target: int) -> int:
        index = lower_bound(nums, target)
        if index == len(nums) or nums[index] != target:
            return -1
        return index
