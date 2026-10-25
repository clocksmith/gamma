class Solution:
    def findGCD(self, nums: list[int]) -> int:
        first = min(nums)
        second = max(nums)
        while second != 0:
            first, second = second, first % second
        return first
