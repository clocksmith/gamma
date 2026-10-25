class Solution:
    def arrayChange(self, nums: list[int], operations: list[list[int]]) -> list[int]:
        positions = {value: index for index, value in enumerate(nums)}
        for previous, replacement in operations:
            index = positions.pop(previous)
            nums[index] = replacement
            positions[replacement] = index
        return nums
