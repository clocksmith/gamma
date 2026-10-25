class Solution:
    def frequencySort(self, nums: list[int]) -> list[int]:
        frequencies = {}
        for value in nums:
            frequencies[value] = frequencies.get(value, 0) + 1
        return sorted(nums, key=lambda value: (frequencies[value], -value))
