class Solution:
    def countBadPairs(self, nums: list[int]) -> int:
        frequencies = {}
        bad = 0
        for index, value in enumerate(nums):
            key = value - index
            good = frequencies.get(key, 0)
            bad += index - good
            frequencies[key] = good + 1
        return bad
