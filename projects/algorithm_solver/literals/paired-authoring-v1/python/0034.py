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


def upper_bound(values: list[int], target: int) -> int:
    left = 0
    right = len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] <= target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def searchRange(self, nums: list[int], target: int) -> list[int]:
        first = lower_bound(nums, target)
        if first == len(nums) or nums[first] != target:
            return [-1, -1]
        last = upper_bound(nums, target) - 1
        return [first, last]
